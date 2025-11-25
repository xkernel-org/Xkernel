#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/DenseSet.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

struct TaintTrackerPass : public PassInfoMixin<TaintTrackerPass> {

    // Pass parameters
    std::string FunctionName;
    std::string TargetOpcode;
    int64_t ConstantToTrack;  // Support both positive and negative constants
    bool Verbose;
    bool InterprocMode;  // Enable downward interprocedural taint tracking (caller -> callee)
    bool IndirectCallMode;  // Enable indirect call (function pointer) analysis
    bool UpwardInterprocMode;  // Enable upward interprocedural taint tracking (callee -> caller)
    unsigned OccurrenceIndex;  // Which occurrence to track (1 = first [default], 2 = second, etc., 0 = all)

    // Constructor with parameters
    TaintTrackerPass(std::string FuncName, std::string Opcode, int64_t Constant, bool Debug, bool Interproc, bool IndirectCall, bool UpwardInterproc, unsigned Occurrence)
        : FunctionName(std::move(FuncName)), TargetOpcode(std::move(Opcode)),
          ConstantToTrack(Constant), Verbose(Debug), InterprocMode(Interproc), IndirectCallMode(IndirectCall), UpwardInterprocMode(UpwardInterproc), OccurrenceIndex(Occurrence) {}

    // Helper to print a value
    std::string getValueName(Value *V) {
        if (!V) return "N/A";
        std::string s;
        raw_string_ostream os(s);
        V->print(os);
        return os.str();
    }

    // Helper to get debug location information
    std::string getDebugLoc(Instruction *I) {
        if (!I) return "";

        const DebugLoc &DL = I->getDebugLoc();
        if (!DL) return "";

        std::string s;
        raw_string_ostream os(s);
        os << " <" << DL->getFilename() << ":" << DL->getLine();
        if (DL->getColumn() != 0) {
            os << ":" << DL->getColumn();
        }
        os << ">";
        return os.str();
    }

    // Helper to check if a value derives from a function parameter (pointer type)
    bool derivesFromPointerParameter(Value *V) {
        if (!V) return false;

        // Direct parameter check
        if (isa<Argument>(V) && V->getType()->isPointerTy()) {
            return true;
        }

        // If it's a load instruction, check what it loads from
        if (LoadInst *LI = dyn_cast<LoadInst>(V)) {
            Value *LoadPtr = LI->getPointerOperand();
            // Check if we're loading from an alloca that stores a parameter
            if (AllocaInst *AI = dyn_cast<AllocaInst>(LoadPtr)) {
                // Look for stores to this alloca
                for (User *U : AI->users()) {
                    if (StoreInst *SI = dyn_cast<StoreInst>(U)) {
                        Value *StoredVal = SI->getValueOperand();
                        if (isa<Argument>(StoredVal) && StoredVal->getType()->isPointerTy()) {
                            return true;
                        }
                    }
                }
            }
        }

        return false;
    }

    // Helper to get which pointer parameter a value derives from (returns parameter, or nullptr if not from param)
    Argument* getPointerParameterOrigin(Value *V) {
        if (!V) return nullptr;

        // Direct parameter check
        if (Argument *Arg = dyn_cast<Argument>(V)) {
            if (Arg->getType()->isPointerTy()) {
                return Arg;
            }
        }

        // If it's a load instruction, check what it loads from
        if (LoadInst *LI = dyn_cast<LoadInst>(V)) {
            Value *LoadPtr = LI->getPointerOperand();
            // Check if we're loading from an alloca that stores a parameter
            if (AllocaInst *AI = dyn_cast<AllocaInst>(LoadPtr)) {
                // Look for stores to this alloca
                for (User *U : AI->users()) {
                    if (StoreInst *SI = dyn_cast<StoreInst>(U)) {
                        Value *StoredVal = SI->getValueOperand();
                        if (Argument *Arg = dyn_cast<Argument>(StoredVal)) {
                            if (Arg->getType()->isPointerTy()) {
                                return Arg;
                            }
                        }
                    }
                }
            }
        }

        return nullptr;
    }

    // Helper to check if two GEP instructions access the same struct field pattern
    bool sameGEPPattern(GetElementPtrInst *GEP1, GetElementPtrInst *GEP2) {
        if (!GEP1 || !GEP2) return false;

        // Check if they have the same number of indices
        if (GEP1->getNumIndices() != GEP2->getNumIndices()) return false;

        // Check if they access the same source element type
        if (GEP1->getSourceElementType() != GEP2->getSourceElementType()) {
            return false;
        }

        // Compare all indices - for struct field access, indices must match
        auto Idx1 = GEP1->idx_begin();
        auto Idx2 = GEP2->idx_begin();
        for (; Idx1 != GEP1->idx_end(); ++Idx1, ++Idx2) {
            // Try to compare constant indices
            if (ConstantInt *C1 = dyn_cast<ConstantInt>(&**Idx1)) {
                if (ConstantInt *C2 = dyn_cast<ConstantInt>(&**Idx2)) {
                    if (C1->getSExtValue() != C2->getSExtValue()) {
                        return false;
                    }
                } else {
                    return false;  // One constant, one not
                }
            } else if (isa<ConstantInt>(&**Idx2)) {
                return false;  // One constant, one not
            }
            // If both are non-constant, we conservatively assume they might match
        }

        // If we get here, the GEPs access the same field of the same struct type
        // This is a conservative match - could be same struct or different instances
        return true;
    }

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {

        SmallVector<Value*, 64> Worklist;
        DenseSet<Value*> TaintedValues;
        DenseSet<Value*> TaintedPointers;  // Track pointers that hold tainted values
        DenseSet<Instruction*> KilledStores;  // Track stores that kill taint (overwrite with non-tainted value)
        DenseSet<Function*> FunctionsReturningTaint;  // Track functions that return tainted values

        // Map from pointer to the instruction that caused it to be tainted (for execution order checking)
        DenseMap<Value*, Instruction*> PointerTaintOrigin;

        // Map from Function to set of parameter indices that receive tainted values via pointer stores
        DenseMap<Function*, DenseSet<unsigned>> FunctionsTaintingPointerParams;

        // Map from function pointer (alloca or global) to set of possible function targets
        DenseMap<Value*, SmallVector<Function*, 4>> FunctionPointerTargets;

        // --- 1. Seed the Worklist ---
        // Find the starting point based on function name, opcode, and constant value
        errs() << "=== Taint Tracker Configuration ===\n";
        errs() << "Function: " << FunctionName << "\n";
        errs() << "Opcode: " << TargetOpcode << "\n";
        errs() << "Constant: " << ConstantToTrack << "\n";
        errs() << "Verbose: " << (Verbose ? "ON" : "OFF") << "\n";
        errs() << "Interproc (downward): " << (InterprocMode ? "ON" : "OFF") << "\n";
        errs() << "Interproc (upward): " << (UpwardInterprocMode ? "ON" : "OFF") << "\n";
        errs() << "IndirectCall: " << (IndirectCallMode ? "ON" : "OFF") << "\n";
        if (OccurrenceIndex == 0) {
            errs() << "Occurrence: ALL\n\n";
        } else {
            errs() << "Occurrence: " << OccurrenceIndex << " (of constant " << ConstantToTrack << ")\n\n";
        }

        // --- Build function pointer target map (if indirect call mode is enabled) ---
        if (IndirectCallMode) {
            if (Verbose) errs() << "=== Building Function Pointer Target Map ===\n";

            for (Function &F : M) {
                if (F.isDeclaration()) continue;

                for (BasicBlock &BB : F) {
                    for (Instruction &I : BB) {
                        // Look for stores where the value being stored is a function
                        if (StoreInst *Store = dyn_cast<StoreInst>(&I)) {
                            Value *StoredVal = Store->getValueOperand();
                            Value *Ptr = Store->getPointerOperand();
                            Value *PtrStripped = Ptr->stripPointerCasts();

                            // Check if storing a function pointer
                            if (Function *Func = dyn_cast<Function>(StoredVal)) {
                                // Track both the original pointer and stripped version
                                // This handles both direct allocas and GEP-based struct fields
                                FunctionPointerTargets[PtrStripped].push_back(Func);
                                if (Ptr != PtrStripped) {
                                    // Also track the GEP result itself for struct field pattern
                                    FunctionPointerTargets[Ptr].push_back(Func);
                                }
                                if (Verbose) {
                                    errs() << "  Found function pointer assignment: "
                                           << getValueName(Ptr) << " <- " << Func->getName() << "\n";
                                }
                            }
                        }
                    }
                }
            }

            if (Verbose) errs() << "\n";
        }

        // Counter for occurrence tracking
        unsigned currentOccurrence = 0;

        for (Function &F : M) {
            if (F.getName() == FunctionName) {
                int NumBB = 0;
                for (BasicBlock &BB : F) {
                    NumBB++;
                    if (Verbose)
                        errs() << "BB " << NumBB << "\n";
                    int NumInst = 0;
                    for (Instruction &I : BB) {
                        NumInst++;
                        std::string OpcodeName = I.getOpcodeName();
                        if (Verbose)
                            errs() << "Inst " << NumInst << ": " << OpcodeName << "\n";
                        if (!TargetOpcode.empty() && OpcodeName != TargetOpcode)
                            continue;
                        int NumOp = 0;
                        for (Value *Op : I.operands()) {
                            NumOp++;
                            if (Verbose) {
                                errs() << "Op " << NumOp << ": " << *Op << "\n";
                            }
                            if (ConstantInt *CI = dyn_cast<ConstantInt>(Op)) {
                                if (CI->getSExtValue() == ConstantToTrack) {
                                    // Increment occurrence counter
                                    currentOccurrence++;

                                    // Skip if this is not the desired occurrence
                                    if (OccurrenceIndex != 0 && currentOccurrence != OccurrenceIndex) {
                                        if (Verbose)
                                            errs() << "  Skipping occurrence " << currentOccurrence
                                                   << " (looking for " << OccurrenceIndex << ")\n";
                                        continue;
                                    }
                                    if (TaintedValues.insert(&I).second) {
                                        Worklist.push_back(&I);
                                        errs() << "[SOURCE] Tainting: " << I << getDebugLoc(&I) << "\n";

                                        // Mark as part of data flow since it's in the worklist
                                        errs() << "[USE] Source instruction in data flow" << getDebugLoc(&I) << "\n";

                                        // If this is a return instruction with the constant, report it
                                        if (ReturnInst *Ret = dyn_cast<ReturnInst>(&I)) {
                                            if (Ret->getReturnValue() == CI) {
                                                errs() << "[RETURN] Constant is returned directly"
                                                       << getDebugLoc(Ret) << "\n";
                                                // Track that this function returns a tainted value
                                                Function *ContainingFunc = Ret->getFunction();
                                                if (ContainingFunc) {
                                                    FunctionsReturningTaint.insert(ContainingFunc);
                                                }
                                            }
                                        }

                                        // If this is a store instruction, check what we're storing to
                                        if (StoreInst *Store = dyn_cast<StoreInst>(&I)) {
                                            Value *Ptr = Store->getPointerOperand()->stripPointerCasts();

                                            // Always mark as store destination for data flow tracking
                                            errs() << "[STORE DESTINATION] Storing constant to: "
                                                   << getValueName(Ptr) << getDebugLoc(Store) << "\n";

                                            // Check if storing to a global variable or pointer parameter (external effects)
                                            if (GlobalVariable *GV = dyn_cast<GlobalVariable>(Ptr)) {
                                                errs() << "[GLOBAL] Constant stored to global variable: "
                                                       << GV->getName() << getDebugLoc(Store) << "\n";
                                            } else if (Argument *PtrParam = getPointerParameterOrigin(Store->getPointerOperand())) {
                                                errs() << "[POINTER PARAMETER] Constant stored through pointer parameter"
                                                       << getDebugLoc(Store) << "\n";
                                                // Track this for upward interprocedural analysis
                                                Function *ContainingFunc = Store->getFunction();
                                                if (ContainingFunc) {
                                                    unsigned ParamIdx = PtrParam->getArgNo();
                                                    FunctionsTaintingPointerParams[ContainingFunc].insert(ParamIdx);
                                                    if (Verbose) {
                                                        errs() << "  Tracking: Function " << ContainingFunc->getName()
                                                               << " taints parameter " << ParamIdx << "\n";
                                                    }
                                                }
                                            } else {
                                                // Local variable - mark pointer as tainted for propagation
                                                if (TaintedPointers.insert(Ptr).second) {
                                                    // Already printed STORE DESTINATION above
                                                    PointerTaintOrigin[Ptr] = Store;
                                                }
                                            }
                                        }

                                        // If this is a call instruction with the constant as an argument
                                        if (CallInst *Call = dyn_cast<CallInst>(&I)) {
                                            Function *Callee = Call->getCalledFunction();
                                            if (Callee) {
                                                // Find which argument position has the constant
                                                for (unsigned ArgIdx = 0; ArgIdx < Call->arg_size(); ++ArgIdx) {
                                                    if (Call->getArgOperand(ArgIdx) == CI) {
                                                        // Report the call
                                                        errs() << "[CHILD FUNCTION] Constant used in call to "
                                                               << Callee->getName() << " at argument " << ArgIdx
                                                               << getDebugLoc(Call) << "\n";

                                                        // In interproc mode, propagate taint to the parameter
                                                        if (InterprocMode && !Callee->isDeclaration()) {
                                                            if (ArgIdx < Callee->arg_size()) {
                                                                Argument *Param = Callee->getArg(ArgIdx);
                                                                if (TaintedValues.insert(Param).second) {
                                                                    Worklist.push_back(Param);
                                                                    errs() << "[INTERPROC] Propagating taint to parameter in "
                                                                           << Callee->getName() << ": "
                                                                           << getValueName(Param) << getDebugLoc(Call) << "\n";
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            } else {
                                                // Indirect call
                                                for (unsigned ArgIdx = 0; ArgIdx < Call->arg_size(); ++ArgIdx) {
                                                    if (Call->getArgOperand(ArgIdx) == CI) {
                                                        errs() << "[CHILD FUNCTION] Constant used in indirect call at argument " << ArgIdx
                                                               << getDebugLoc(Call) << "\n";
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    // If tracking a specific occurrence, exit after finding it
                                    if (OccurrenceIndex != 0) {
                                        goto found;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

found:

        // --- 2. Run the Worklist Algorithm with Load Tracking ---
        // Keep track of which pointers we've already scanned for loads
        DenseSet<Value*> ScannedPointers;

        // Iterate until we reach a fixed point (no new tainted pointers)
        bool changed = true;
        while (changed) {
            changed = false;

            // Process the worklist
            while (!Worklist.empty()) {
                Value *V = Worklist.pop_back_val();

                if (!V->user_empty())
                    errs() << "[USE] Processing uses of: " << getValueName(V) << "\n";
                else
                    errs() << "[NO USE] No uses of: " << getValueName(V) << "\n";

                for (User *U : V->users()) {
                    if (Instruction *UserInst = dyn_cast<Instruction>(U)) {
                        if (Verbose)
                            errs() << "  [USER] Processing use: " << getValueName(U) << "\n";

                        // --- Check for Sinks (Stop at function calls in non-interproc mode) ---
                        if (CallInst *Call = dyn_cast<CallInst>(UserInst)) {
                            bool isArg = false;
                            unsigned argIdx = 0;
                            for (unsigned i = 0; i < Call->arg_size(); ++i) {
                                if (Call->getArgOperand(i) == V) {
                                    isArg = true;
                                    argIdx = i;
                                    break;
                                }
                            }
                            if (isArg) {
                                Function *Callee = Call->getCalledFunction();
                                if (Callee && !Callee->isDeclaration()) {
                                    // Direct call to a defined function
                                    // Report the call
                                    errs() << "  [CHILD FUNCTION] Tainted value used in call to "
                                           << Callee->getName() << " at argument " << argIdx
                                           << getDebugLoc(Call) << "\n";

                                    // In interproc mode, propagate taint to the parameter
                                    if (InterprocMode) {
                                        if (argIdx < Callee->arg_size()) {
                                            Argument *Param = Callee->getArg(argIdx);
                                            if (TaintedValues.insert(Param).second) {
                                                Worklist.push_back(Param);
                                                errs() << "  [INTERPROC] Propagating taint to parameter in "
                                                       << Callee->getName() << ": "
                                                       << getValueName(Param) << getDebugLoc(Call) << "\n";
                                                changed = true;
                                            }
                                        }
                                    }
                                } else if (!Callee && IndirectCallMode && InterprocMode) {
                                    // Indirect call (function pointer) - try to resolve targets
                                    Value *CalledValue = Call->getCalledOperand();

                                    // Try to trace back to the function pointer
                                    SmallVector<Function*, 4> Targets;

                                    // Check if it's a direct load from a tracked pointer
                                    if (LoadInst *Load = dyn_cast<LoadInst>(CalledValue)) {
                                        Value *LoadPtr = Load->getPointerOperand();
                                        Value *LoadPtrStripped = LoadPtr->stripPointerCasts();

                                        // Try both the original pointer (for GEP/struct fields) and stripped version
                                        if (FunctionPointerTargets.count(LoadPtr)) {
                                            Targets = FunctionPointerTargets[LoadPtr];
                                        } else if (FunctionPointerTargets.count(LoadPtrStripped)) {
                                            Targets = FunctionPointerTargets[LoadPtrStripped];
                                        } else if (GetElementPtrInst *LoadGEP = dyn_cast<GetElementPtrInst>(LoadPtr)) {
                                            // For GEP-based loads (struct fields), try to match the pattern
                                            for (auto &Entry : FunctionPointerTargets) {
                                                if (GetElementPtrInst *StoreGEP = dyn_cast<GetElementPtrInst>(Entry.first)) {
                                                    if (sameGEPPattern(LoadGEP, StoreGEP)) {
                                                        // Found a matching GEP pattern
                                                        Targets = Entry.second;
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    if (!Targets.empty()) {
                                        errs() << "  [INDIRECT CALL] Tainted value used in indirect call"
                                               << getDebugLoc(Call) << " (resolved to " << Targets.size() << " target(s))\n";

                                        // Propagate to all possible targets
                                        for (Function *Target : Targets) {
                                            if (Target->isDeclaration()) continue;

                                            errs() << "    [INDIRECT TARGET] " << Target->getName() << "\n";

                                            if (argIdx < Target->arg_size()) {
                                                Argument *Param = Target->getArg(argIdx);
                                                if (TaintedValues.insert(Param).second) {
                                                    Worklist.push_back(Param);
                                                    errs() << "    [INTERPROC] Propagating taint to parameter in "
                                                           << Target->getName() << ": "
                                                           << getValueName(Param) << getDebugLoc(Call) << "\n";
                                                    changed = true;
                                                }
                                            }
                                        }
                                    } else {
                                        // IndirectCallMode is ON but couldn't resolve targets (unknown assignment)
                                        errs() << "  [EXTERNAL CALL] Tainted value used in external/unresolved indirect call: "
                                               << *Call << getDebugLoc(Call) << "\n";
                                    }
                                } else {
                                    // Either external function, or indirect call without analysis enabled
                                    errs() << "  [EXTERNAL CALL] Tainted value used in external/indirect call: "
                                           << *Call << getDebugLoc(Call) << "\n";
                                }
                                // In non-interproc mode, don't propagate the call further
                                if (!InterprocMode) {
                                    continue;
                                }
                            }
                        }
                        if (ReturnInst *Ret = dyn_cast<ReturnInst>(UserInst)) {
                            if (Ret->getReturnValue() == V) {
                                errs() << "  [RETURN] Stop: Tainted value is returned: "
                                       << getValueName(Ret) << getDebugLoc(Ret) << "\n";
                                // Track that this function returns a tainted value
                                Function *ContainingFunc = Ret->getFunction();
                                if (ContainingFunc) {
                                    FunctionsReturningTaint.insert(ContainingFunc);
                                }
                                continue;
                            }
                        }
                        if (StoreInst *Store = dyn_cast<StoreInst>(UserInst)) {
                            if (Store->getValueOperand() == V) {
                                Value *Ptr = Store->getPointerOperand()->stripPointerCasts();
                                if (GlobalVariable *GV = dyn_cast<GlobalVariable>(Ptr)) {
                                    errs() << "  [GLOBAL] Tainted value stored to global variable: "
                                           << GV->getName() << getDebugLoc(Store) << "\n";
                                    continue;
                                }
                                if (Argument *PtrParam = getPointerParameterOrigin(Store->getPointerOperand())) {
                                    errs() << "  [POINTER PARAMETER] Tainted value stored through pointer parameter"
                                           << getDebugLoc(Store) << "\n";
                                    // Track this for upward interprocedural analysis
                                    Function *ContainingFunc = Store->getFunction();
                                    if (ContainingFunc) {
                                        unsigned ParamIdx = PtrParam->getArgNo();
                                        FunctionsTaintingPointerParams[ContainingFunc].insert(ParamIdx);
                                        if (Verbose) {
                                            errs() << "    Tracking: Function " << ContainingFunc->getName()
                                                   << " taints parameter " << ParamIdx << "\n";
                                        }
                                    }
                                    continue;
                                }
                                // For local variables, mark the pointer as tainted
                                // This allows us to track through variable assignments
                                if (TaintedPointers.insert(Ptr).second) {
                                    errs() << "  [STORE DESTINATION] Marking pointer as tainted: "
                                           << getValueName(Ptr) << getDebugLoc(Store) << "\n";
                                    PointerTaintOrigin[Ptr] = Store;
                                    changed = true;  // We found a new tainted pointer
                                }
                            }
                        }

                        // --- Propagate Taint ---
                        if (TaintedValues.insert(UserInst).second) {
                            Worklist.push_back(UserInst);
                            errs() << "  [USE] Taint flows to: " << getValueName(UserInst) << getDebugLoc(UserInst) << "\n";
                        }
                    }
                }
            }

            // --- Identify Kill Stores ---
            // Find stores to tainted pointers where the stored value is NOT tainted
            // These "kill" the taint for that pointer
            for (Function &F : M) {
                if (F.isDeclaration()) continue;  // Skip declarations
                for (BasicBlock &BB : F) {
                    for (Instruction &I : BB) {
                        if (StoreInst *Store = dyn_cast<StoreInst>(&I)) {
                            Value *StoredVal = Store->getValueOperand();
                            Value *Ptr = Store->getPointerOperand()->stripPointerCasts();

                            // If we're storing to a tainted pointer, but the value is NOT tainted
                            // This is a kill - it overwrites the tainted value
                            if (TaintedPointers.count(Ptr) && !TaintedValues.count(StoredVal)) {
                                // Only kill if this is not the original source store
                                // (Check that this store itself is not tainted)
                                if (!TaintedValues.count(Store)) {
                                    KilledStores.insert(Store);
                                    errs() << "[KILL] Store overwrites tainted pointer with non-tainted value: "
                                           << getValueName(Store) /* << getDebugLoc(Store) */<< "\n";
                                }
                            }
                        }
                    }
                }
            }

            // Scan for loads from newly tainted pointers
            // But skip loads that happen after a kill store
            DenseSet<Value*> PointersToScan;
            for (Value *Ptr : TaintedPointers) {
                if (!ScannedPointers.count(Ptr)) {
                    PointersToScan.insert(Ptr);
                }
            }

            for (Function &F : M) {
                if (F.isDeclaration()) continue;  // Skip declarations
                for (BasicBlock &BB : F) {
                    for (Instruction &I : BB) {
                        if (LoadInst *Load = dyn_cast<LoadInst>(&I)) {
                            Value *Ptr = Load->getPointerOperand()->stripPointerCasts();
                            // Only process if this pointer needs to be scanned
                            if (PointersToScan.count(Ptr)) {

                                // Check if this load happens after a kill store to the same pointer
                                bool afterKill = false;
                                for (Instruction *KillStore : KilledStores) {
                                    Value *KillPtr = cast<StoreInst>(KillStore)->getPointerOperand()->stripPointerCasts();
                                    if (KillPtr == Ptr) {
                                        // Check if Load comes after KillStore in the same basic block
                                        if (Load->getParent() == KillStore->getParent()) {
                                            // Simple ordering: iterate through BB and check which comes first
                                            for (Instruction &CheckI : *Load->getParent()) {
                                                if (&CheckI == KillStore) {
                                                    // Kill store comes first, check if load comes after
                                                    break;
                                                }
                                                if (&CheckI == Load) {
                                                    // Load comes first, so it's before the kill
                                                    break;
                                                }
                                            }
                                            // Check again properly
                                            bool foundKill = false;
                                            for (Instruction &CheckI : *Load->getParent()) {
                                                if (&CheckI == KillStore) {
                                                    foundKill = true;
                                                }
                                                if (&CheckI == Load && foundKill) {
                                                    afterKill = true;
                                                    break;
                                                }
                                            }
                                        }
                                        // TODO: Handle cross-basic-block dominance properly
                                        // For now, just handle same-BB case
                                    }
                                }

                                if (afterKill) {
                                    errs() << "[SKIP] Load after kill, not tainting: "
                                           << getValueName(Load) << /* getDebugLoc(Load) << */ "\n";
                                    continue;
                                }

                                // Check if this load happens before the instruction that tainted the pointer
                                bool beforeTaintOrigin = false;
                                if (PointerTaintOrigin.count(Ptr)) {
                                    Instruction *TaintOrigin = PointerTaintOrigin[Ptr];
                                    // Check if Load comes before TaintOrigin in the same basic block
                                    if (Load->getParent() == TaintOrigin->getParent()) {
                                        bool foundLoad = false;
                                        for (Instruction &CheckI : *Load->getParent()) {
                                            if (&CheckI == Load) {
                                                foundLoad = true;
                                            }
                                            if (&CheckI == TaintOrigin && foundLoad) {
                                                beforeTaintOrigin = true;
                                                break;
                                            }
                                        }
                                    }
                                    // TODO: Handle cross-basic-block dominance properly
                                    // For now, just handle same-BB case
                                }

                                if (beforeTaintOrigin) {
                                    errs() << "[SKIP] Load before taint origin, not tainting: "
                                           << getValueName(Load) << getDebugLoc(Load) << "\n";
                                    continue;
                                }

                                if (TaintedValues.insert(Load).second) {
                                    errs() << "[LOAD] Tainted load from tracked pointer: "
                                           << getValueName(Load)
                                           << " ("
                                           << *Ptr
                                           << ") "
                                           << getDebugLoc(Load) << "\n";
                                    Worklist.push_back(Load);
                                    changed = true;
                                }
                            }
                        }
                    }
                }
            }

            // Mark the pointers we just scanned
            for (Value *Ptr : PointersToScan) {
                ScannedPointers.insert(Ptr);
            }
        }

        // --- 5. Upward Interprocedural Taint Tracking (Callee -> Caller) ---
        if (UpwardInterprocMode && (!FunctionsReturningTaint.empty() || !FunctionsTaintingPointerParams.empty())) {
            if (Verbose) errs() << "=== Upward Interprocedural Tracking ===\n";

            // 5a. Find all call sites to functions that return tainted values
            for (Function *TaintedFunc : FunctionsReturningTaint) {
                if (Verbose) {
                    errs() << "Finding callers of: " << TaintedFunc->getName() << " (returns taint)\n";
                }

                // Scan all functions for calls to TaintedFunc
                for (Function &F : M) {
                    if (F.isDeclaration()) continue;

                    for (BasicBlock &BB : F) {
                        for (Instruction &I : BB) {
                            if (CallInst *Call = dyn_cast<CallInst>(&I)) {
                                Function *Callee = Call->getCalledFunction();
                                if (Callee == TaintedFunc) {
                                    // This call site returns a tainted value
                                    if (!TaintedValues.count(Call)) {
                                        errs() << "[UPWARD-INTERPROC] Call to " << TaintedFunc->getName()
                                               << " returns tainted value" << getDebugLoc(Call) << "\n";
                                        TaintedValues.insert(Call);
                                        Worklist.push_back(Call);
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 5b. Find all call sites to functions that taint pointer parameters
            for (auto &Entry : FunctionsTaintingPointerParams) {
                Function *TaintedFunc = Entry.first;
                DenseSet<unsigned> &TaintedParams = Entry.second;

                if (Verbose) {
                    errs() << "Finding callers of: " << TaintedFunc->getName() << " (taints pointer params)\n";
                }

                // Scan all functions for calls to TaintedFunc
                for (Function &F : M) {
                    if (F.isDeclaration()) continue;

                    for (BasicBlock &BB : F) {
                        for (Instruction &I : BB) {
                            if (CallInst *Call = dyn_cast<CallInst>(&I)) {
                                Function *Callee = Call->getCalledFunction();
                                if (Callee == TaintedFunc) {
                                    // Check each tainted parameter
                                    for (unsigned ParamIdx : TaintedParams) {
                                        if (ParamIdx >= Call->arg_size()) continue;

                                        Value *ActualArg = Call->getArgOperand(ParamIdx);

                                        // Check if the argument is an address-of operation (alloca, GEP, etc.)
                                        // We need to find what variable this points to
                                        Value *PointedVar = nullptr;
                                        if (AllocaInst *AI = dyn_cast<AllocaInst>(ActualArg)) {
                                            PointedVar = AI;
                                        } else if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(ActualArg)) {
                                            PointedVar = GEP->getPointerOperand()->stripPointerCasts();
                                        }

                                        if (PointedVar) {
                                            if (TaintedPointers.insert(PointedVar).second) {
                                                errs() << "[UPWARD-INTERPROC] Call to " << TaintedFunc->getName()
                                                       << " taints argument " << ParamIdx << " (pointer parameter)"
                                                       << getDebugLoc(Call) << "\n";
                                                errs() << "  [STORE DESTINATION] Marking pointer as tainted via call: "
                                                       << getValueName(PointedVar) << "\n";
                                                PointerTaintOrigin[PointedVar] = Call;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Process the new worklist items (call sites that return tainted values)
            // This uses the same propagation logic as the main worklist
            DenseSet<Value*> UpwardScannedPointers;

            // Loop: process worklist, then scan for loads, repeat until fixed point
            while (true) {
                // Process worklist items
                while (!Worklist.empty()) {
                    Value *V = Worklist.back();
                    Worklist.pop_back();

                    if (Verbose) errs() << "[USE] Processing uses of: " << getValueName(V) << "\n";

                    bool hasUses = false;
                    for (User *U : V->users()) {
                        Instruction *UserInst = dyn_cast<Instruction>(U);
                        if (!UserInst) continue;

                        if (TaintedValues.count(UserInst)) {
                            if (Verbose) errs() << "  [SKIP] Already tainted: " << getValueName(UserInst) << "\n";
                            continue;
                        }

                        hasUses = true;
                        errs() << "  [USE] Taint flows to: " << getValueName(UserInst) << getDebugLoc(UserInst) << "\n";
                        TaintedValues.insert(UserInst);

                        // Handle store instructions - mark destination pointer as tainted
                        if (StoreInst *Store = dyn_cast<StoreInst>(UserInst)) {
                            if (Store->getValueOperand() == V) {
                                Value *Ptr = Store->getPointerOperand()->stripPointerCasts();
                                if (TaintedPointers.insert(Ptr).second) {
                                    PointerTaintOrigin[Ptr] = Store;
                                }
                            }
                        }

                        Worklist.push_back(UserInst);
                    }

                    if (!hasUses && Verbose) {
                        errs() << "[NO USE] No uses of: " << getValueName(V) << "\n";
                    }
                }

                // Scan for loads from tainted pointers
                SmallVector<Value*, 16> PointersToScan;
                for (Value *Ptr : TaintedPointers) {
                    if (!UpwardScannedPointers.count(Ptr)) {
                        PointersToScan.push_back(Ptr);
                    }
                }

                if (PointersToScan.empty()) break;  // Fixed point reached

                for (Value *Ptr : PointersToScan) {
                    for (Function &F : M) {
                        if (F.isDeclaration()) continue;

                        for (BasicBlock &BB : F) {
                            for (Instruction &I : BB) {
                                if (LoadInst *Load = dyn_cast<LoadInst>(&I)) {
                                    Value *LoadPtr = Load->getPointerOperand()->stripPointerCasts();
                                    if (LoadPtr == Ptr) {
                                        if (!TaintedValues.count(Load)) {
                                            // Check if this load happens before the instruction that tainted the pointer
                                            bool beforeTaintOrigin = false;
                                            if (PointerTaintOrigin.count(Ptr)) {
                                                Instruction *TaintOrigin = PointerTaintOrigin[Ptr];
                                                // Check if Load comes before TaintOrigin in the same basic block
                                                if (Load->getParent() == TaintOrigin->getParent()) {
                                                    bool foundLoad = false;
                                                    for (Instruction &CheckI : *Load->getParent()) {
                                                        if (&CheckI == Load) {
                                                            foundLoad = true;
                                                        }
                                                        if (&CheckI == TaintOrigin && foundLoad) {
                                                            beforeTaintOrigin = true;
                                                            break;
                                                        }
                                                    }
                                                }
                                            }

                                            if (beforeTaintOrigin) {
                                                errs() << "[SKIP] Load before taint origin, not tainting: "
                                                       << getValueName(Load) << getDebugLoc(Load) << "\n";
                                                continue;
                                            }

                                            errs() << "[LOAD] Tainted load from tracked pointer: "
                                                   << getValueName(Load) << " (" << getValueName(Ptr) << ") "
                                                   << getDebugLoc(Load) << "\n";
                                            TaintedValues.insert(Load);
                                            Worklist.push_back(Load);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                for (Value *Ptr : PointersToScan) {
                    UpwardScannedPointers.insert(Ptr);
                }
            }

            if (Verbose) errs() << "\n";
        }

        errs() << "\n=== Taint Analysis Complete ===\n";

        // Return PreservedAnalyses::all() because we didn't modify the IR
        return PreservedAnalyses::all();
    }
};

// --- New Pass Manager Registration ---
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        LLVM_PLUGIN_API_VERSION, "TaintTrackerPass", LLVM_VERSION_STRING,
        [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &MPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                    // Parse: taint-tracker<function_name;opcode;constant_value;debug;interproc;indirectcall;upward_interproc;occurrence>
                    if (Name.consume_front("taint-tracker")) {
                        std::string FunctionName = "gss_fill_context";  // default
                        std::string Opcode = "";  // default (empty means all opcodes)
                        int64_t Constant = 3600;  // default (supports negative values)
                        bool Debug = false;  // default
                        bool Interproc = false;  // default (downward: caller -> callee)
                        bool IndirectCall = false;  // default
                        bool UpwardInterproc = false;  // default (upward: callee -> caller)
                        unsigned Occurrence = 1;  // default (1 = first occurrence, 0 = all occurrences)

                        if (Name.consume_front("<") && Name.consume_back(">")) {
                            // Parse parameters separated by semicolons
                            SmallVector<StringRef, 8> Params;
                            Name.split(Params, ';', -1, true);

                            if (Params.size() >= 1 && !Params[0].empty()) {
                                FunctionName = Params[0].str();
                            }
                            if (Params.size() >= 2 && !Params[1].empty()) {
                                Opcode = Params[1].str();
                            }
                            if (Params.size() >= 3 && !Params[2].empty()) {
                                if (Params[2].getAsInteger(10, Constant)) {
                                    errs() << "Warning: Invalid constant value, using default 3600\n";
                                    Constant = 3600;
                                }
                            }
                            if (Params.size() >= 4 && !Params[3].empty()) {
                                StringRef DebugStr = Params[3];
                                Debug = (DebugStr == "true" || DebugStr == "1" ||
                                        DebugStr == "TRUE" || DebugStr == "yes");
                            }
                            if (Params.size() >= 5 && !Params[4].empty()) {
                                StringRef InterprocStr = Params[4];
                                Interproc = (InterprocStr == "true" || InterprocStr == "1" ||
                                            InterprocStr == "TRUE" || InterprocStr == "yes");
                            }
                            if (Params.size() >= 6 && !Params[5].empty()) {
                                StringRef IndirectCallStr = Params[5];
                                IndirectCall = (IndirectCallStr == "true" || IndirectCallStr == "1" ||
                                               IndirectCallStr == "TRUE" || IndirectCallStr == "yes");
                            }
                            if (Params.size() >= 7 && !Params[6].empty()) {
                                StringRef UpwardInterprocStr = Params[6];
                                UpwardInterproc = (UpwardInterprocStr == "true" || UpwardInterprocStr == "1" ||
                                                  UpwardInterprocStr == "TRUE" || UpwardInterprocStr == "yes");
                            }
                            if (Params.size() >= 8 && !Params[7].empty()) {
                                if (Params[7].getAsInteger(10, Occurrence)) {
                                    errs() << "Warning: Invalid occurrence value, using default 1 (first)\n";
                                    Occurrence = 1;
                                }
                            }
                        }

                        MPM.addPass(TaintTrackerPass(FunctionName, Opcode, Constant, Debug, Interproc, IndirectCall, UpwardInterproc, Occurrence));
                        return true;
                    }
                    return false;
                });
        }
    };
}
