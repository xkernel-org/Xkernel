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
#include "llvm/ADT/STLExtras.h"
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
        os.flush();

        std::size_t pos = s.find(" !dbg !");
        if (pos != std::string::npos) {
            // Include a leading ", " if present so we don't leave a dangling comma.
            std::size_t start = pos;
            if (start >= 2 && s[start - 2] == ',' && s[start - 1] == ' ')
                start -= 2;

            // The debug location normally runs to the end of the line.
            std::size_t end = s.find('\n', pos);
            if (end == std::string::npos) {
                // No newline: just erase to end of string.
                s.erase(start);
            } else {
                // Erase just the " , !dbg !N" part and leave the newline.
                s.erase(start, end - start);
            }
        }

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

    // Helper to get the level of a value
    int getLevel(Value *V, DenseMap<Value*, int> &ValueLevel, DenseMap<Function*, int> &FunctionLevel) {
        if (!V) return 0;

        if (ValueLevel.count(V)) {
            return ValueLevel[V];
        }

        if (Instruction *I = dyn_cast<Instruction>(V)) {
            Function *F = I->getFunction();
            if (F && FunctionLevel.count(F)) {
                return FunctionLevel[F];
            }
        } else if (Argument *Arg = dyn_cast<Argument>(V)) {
            Function *F = Arg->getParent();
            if (F && FunctionLevel.count(F)) {
                return FunctionLevel[F];
            }
        }

        return 0;
    }

    // Helper to get function name and level info for an instruction
    std::string getFuncLevel(Instruction *I, DenseMap<Value*, int> &ValueLevel, DenseMap<Function*, int> &FunctionLevel) {
        if (!I) return "";

        Function *F = I->getFunction();
        if (!F) return "";

        int level = getLevel(I, ValueLevel, FunctionLevel);

        std::string s;
        raw_string_ostream os(s);
        os << " FUNC=" << F->getName() << " L=" << level;
        return os.str();
    }

    // Helper to get function name and level info for a value (works with Instruction or Argument)
    std::string getFuncLevelForValue(Value *V, DenseMap<Value*, int> &ValueLevel, DenseMap<Function*, int> &FunctionLevel) {
        if (!V) return "";

        Function *F = nullptr;
        if (Instruction *I = dyn_cast<Instruction>(V)) {
            F = I->getFunction();
        } else if (Argument *Arg = dyn_cast<Argument>(V)) {
            F = Arg->getParent();
        }

        if (!F) return "";

        int level = getLevel(V, ValueLevel, FunctionLevel);

        std::string s;
        raw_string_ostream os(s);
        os << " FUNC=" << F->getName() << " L=" << level;
        return os.str();
    }

    // Helper to check if a value derives from a function parameter (pointer type)
    bool derivesFromPointerParameter(Value *V) {
        if (!V) return false;

        // Strip pointer casts
        V = V->stripPointerCasts();

        // Direct parameter check
        if (isa<Argument>(V) && V->getType()->isPointerTy()) {
            return true;
        }

        // If it's a GEP (struct field access), check the base pointer
        if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(V)) {
            return derivesFromPointerParameter(GEP->getPointerOperand());
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

    // Helper to extract struct field indices from a GEP chain
    // Returns the field indices accessed (e.g., for s->x->y, returns [field_x, field_y])
    SmallVector<int64_t, 4> extractStructFieldIndices(Value *V, DenseSet<Value*> *Visited = nullptr, bool Debug = false) {
        SmallVector<int64_t, 4> indices;
        if (!V) return indices;

        DenseSet<Value*> LocalVisited;
        if (!Visited) {
            Visited = &LocalVisited;
        }
        if (!Visited->insert(V).second) {
            return indices;  // Already visited
        }

        // Don't strip pointer casts - we need to preserve GEPs for field index extraction
        // V = V->stripPointerCasts();

        // If it's a GEP, extract the field index
        if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(V)) {
            // First recurse on the base to get its indices
            indices = extractStructFieldIndices(GEP->getPointerOperand(), Visited, Debug);

            // Then add this GEP's field index (last index for struct field access)
            if (GEP->getNumIndices() >= 2) {
                // For struct access, the last index is the field
                auto IdxIter = GEP->idx_begin();
                std::advance(IdxIter, GEP->getNumIndices() - 1);
                if (ConstantInt *CI = dyn_cast<ConstantInt>(&**IdxIter)) {
                    indices.push_back(CI->getSExtValue());
                }
            }
        }
        // If it's a load, check what we're loading from
        else if (LoadInst *LI = dyn_cast<LoadInst>(V)) {
            // Don't strip pointer casts here because we need to preserve GEPs to extract field indices
            Value *LoadPtr = LI->getPointerOperand();
            if (AllocaInst *AI = dyn_cast<AllocaInst>(LoadPtr)) {
                // Look for stores to this alloca
                for (User *U : AI->users()) {
                    if (StoreInst *SI = dyn_cast<StoreInst>(U)) {
                        Value *StoredVal = SI->getValueOperand()->stripPointerCasts();
                        auto storedIndices = extractStructFieldIndices(StoredVal, Visited, Debug);
                        if (!storedIndices.empty()) {
                            return storedIndices;
                        }
                    }
                }
                // If no stored values had indices, return empty
                return indices;
            } else {
                return extractStructFieldIndices(LoadPtr, Visited, Debug);
            }
        }

        return indices;
    }

    // Helper to get which pointer parameter a value derives from (returns parameter, or nullptr if not from param)
    Argument* getPointerParameterOrigin(Value *V, DenseSet<Value*> *Visited = nullptr) {
        if (!V) return nullptr;

        // Track visited values to avoid infinite loops
        DenseSet<Value*> LocalVisited;
        if (!Visited) {
            Visited = &LocalVisited;
        }
        if (!Visited->insert(V).second) {
            return nullptr;  // Already visited
        }

        // Strip pointer casts
        V = V->stripPointerCasts();

        // Direct parameter check
        if (Argument *Arg = dyn_cast<Argument>(V)) {
            if (Arg->getType()->isPointerTy()) {
                return Arg;
            }
        }

        // If it's a GEP (struct field access), check the base pointer
        if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(V)) {
            return getPointerParameterOrigin(GEP->getPointerOperand(), Visited);
        }

        // If it's a load instruction, check what it loads from
        if (LoadInst *LI = dyn_cast<LoadInst>(V)) {
            Value *LoadPtr = LI->getPointerOperand()->stripPointerCasts();

            // Check if we're loading from an alloca that stores a parameter (or something derived from a parameter)
            if (AllocaInst *AI = dyn_cast<AllocaInst>(LoadPtr)) {
                // Look for stores to this alloca
                for (User *U : AI->users()) {
                    if (StoreInst *SI = dyn_cast<StoreInst>(U)) {
                        Value *StoredVal = SI->getValueOperand()->stripPointerCasts();

                        // Direct parameter store
                        if (Argument *Arg = dyn_cast<Argument>(StoredVal)) {
                            if (Arg->getType()->isPointerTy()) {
                                return Arg;
                            }
                        }

                        // Recursively check if the stored value derives from a parameter
                        // This handles cases like: int *y = x; where x is a parameter
                        if (Argument *Arg = getPointerParameterOrigin(StoredVal, Visited)) {
                            return Arg;
                        }
                    }
                }
            }
            // Also check if we're loading from a pointer that itself derives from a parameter
            // This handles: int *y = s->x; where s is a parameter
            // LoadPtr could be a GEP on a parameter, so recursively check it
            else if (Argument *Arg = getPointerParameterOrigin(LoadPtr, Visited)) {
                return Arg;
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

    // Helper to get sorted users for deterministic output
    SmallVector<User*, 16> getSortedUsers(Value *V) {
        SmallVector<User*, 16> SortedUsers(V->user_begin(), V->user_end());
        llvm::sort(SortedUsers, [](User *A, User *B) {
            return std::less<User*>()(A, B);
        });
        return SortedUsers;
    }

    // Helper to check if a load comes before the taint origin instruction (same BB only)
    bool isLoadBeforeTaintOrigin(LoadInst *Load, Value *Ptr,
                                  const DenseMap<Value*, Instruction*>& PointerTaintOrigin) {
        if (!PointerTaintOrigin.count(Ptr)) return false;

        Instruction *TaintOrigin = PointerTaintOrigin.lookup(Ptr);
        if (Load->getParent() != TaintOrigin->getParent()) return false;

        bool foundLoad = false;
        for (Instruction &I : *Load->getParent()) {
            if (&I == Load) foundLoad = true;
            if (&I == TaintOrigin && foundLoad) return true;
        }
        return false;
    }

    // Helper to ensure level is set for an instruction based on its function
    void ensureLevelSet(Instruction *I, DenseMap<Value*, int>& ValueLevel,
                        DenseMap<Function*, int>& FunctionLevel) {
        if (ValueLevel.count(I)) return;

        Function *F = I->getFunction();
        if (F && FunctionLevel.count(F)) {
            ValueLevel[I] = FunctionLevel[F];
        }
    }

    // Helper to process a store instruction for taint propagation
    bool processStoreForTaint(StoreInst *Store, Value *V,
                              DenseSet<Value*>& TaintedPointers,
                              DenseMap<Value*, Instruction*>& PointerTaintOrigin,
                              DenseMap<Function*, DenseSet<unsigned>>& FunctionsTaintingPointerParams,
                              DenseMap<Function*, DenseMap<unsigned, SmallVector<int64_t, 4>>>& FunctionParamFieldAccess,
                              DenseMap<Value*, int>& ValueLevel,
                              DenseMap<Function*, int>& FunctionLevel) {
        if (Store->getValueOperand() != V) return false;

        bool discoveredNew = false;
        Value *Ptr = Store->getPointerOperand()->stripPointerCasts();

        // Mark pointer as tainted
        if (TaintedPointers.insert(Ptr).second) {
            PointerTaintOrigin[Ptr] = Store;
            errs() << "  [STORE DESTINATION] Marking pointer as tainted: "
                   << getValueName(Ptr) << getDebugLoc(Store)
                   << getFuncLevel(Store, ValueLevel, FunctionLevel) << "\n";
        }

                        // Check for pointer parameter tainting
                        if (Argument *PtrParam = getPointerParameterOrigin(Store->getPointerOperand())) {
                            Function *ContainingFunc = Store->getFunction();
                            if (ContainingFunc) {
                                unsigned ParamIdx = PtrParam->getArgNo();
                                errs() << "  [POINTER PARAMETER] Tainted value stored through pointer parameter"
                                       << getDebugLoc(Store) << getFuncLevel(Store, ValueLevel, FunctionLevel) << "\n";
                                if (FunctionsTaintingPointerParams[ContainingFunc].insert(ParamIdx).second) {
                                    discoveredNew = true;
                                }
                                // Track which struct fields are accessed
                                SmallVector<int64_t, 4> fieldIndices = extractStructFieldIndices(Store->getPointerOperand(), nullptr, false);
                                if (!fieldIndices.empty()) {
                                    DenseMap<unsigned, SmallVector<int64_t, 4>> &funcMap = FunctionParamFieldAccess[ContainingFunc];
                                    SmallVector<int64_t, 4> &existingIndices = funcMap[ParamIdx];
                                    for (int64_t idx : fieldIndices) {
                                        if (std::find(existingIndices.begin(), existingIndices.end(), idx) == existingIndices.end()) {
                                            existingIndices.push_back(idx);
                                        }
                                    }
                                }
                            }
                        }

        return discoveredNew;
    }

    // Helper to scan loads from a list of tainted pointers
    bool scanLoadsFromTaintedPointers(const SmallVector<Value*, 32>& PointersToScan,
                                      Module& M,
                                      DenseSet<Value*>& TaintedValues,
                                      DenseMap<Value*, Instruction*>& PointerTaintOrigin,
                                      DenseMap<Value*, int>& ValueLevel,
                                      DenseMap<Function*, int>& FunctionLevel,
                                      SmallVector<Value*, 64>& Worklist,
                                      const DenseSet<Instruction*>* KilledStores = nullptr) {
        bool changed = false;

        for (Value *Ptr : PointersToScan) {
            for (Function &F : M) {
                if (F.isDeclaration()) continue;

                for (BasicBlock &BB : F) {
                    for (Instruction &I : BB) {
                        LoadInst *Load = dyn_cast<LoadInst>(&I);
                        if (!Load) continue;

                        Value *LoadPtr = Load->getPointerOperand()->stripPointerCasts();
                        bool matchesPtr = (LoadPtr == Ptr);
                        bool isStructField = false;
                        Value *TaintedBasePtr = nullptr;

                        // Check for GEP-based struct field access
                        if (!matchesPtr) {
                            if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(LoadPtr)) {
                                Value *BasePtr = GEP->getPointerOperand()->stripPointerCasts();
                                if (BasePtr == Ptr) {
                                    matchesPtr = true;
                                    isStructField = true;
                                    TaintedBasePtr = Ptr;
                                }
                            }
                        }

                        if (!matchesPtr) continue;
                        if (TaintedValues.count(Load)) continue;

                        Value *CheckPtr = TaintedBasePtr ? TaintedBasePtr : Ptr;

                        // Check if this load happens after a kill store (if kill tracking is enabled)
                        if (KilledStores) {
                            bool afterKill = false;
                            SmallVector<Instruction*, 16> SortedKilledStores(KilledStores->begin(), KilledStores->end());
                            llvm::sort(SortedKilledStores, [](Instruction *A, Instruction *B) {
                                return std::less<Instruction*>()(A, B);
                            });
                            for (Instruction *KillStore : SortedKilledStores) {
                                Value *KillPtr = cast<StoreInst>(KillStore)->getPointerOperand()->stripPointerCasts();
                                if (KillPtr == CheckPtr && Load->getParent() == KillStore->getParent()) {
                                    bool foundKill = false;
                                    for (Instruction &CheckI : *Load->getParent()) {
                                        if (&CheckI == KillStore) foundKill = true;
                                        if (&CheckI == Load && foundKill) {
                                            afterKill = true;
                                            break;
                                        }
                                    }
                                }
                            }

                            if (afterKill) {
                                ensureLevelSet(Load, ValueLevel, FunctionLevel);
                                errs() << "[SKIP] Load after kill, not tainting: "
                                       << getValueName(Load) << getDebugLoc(Load)
                                       << getFuncLevel(Load, ValueLevel, FunctionLevel) << "\n";
                                continue;
                            }
                        }

                        // Check execution order
                        if (isLoadBeforeTaintOrigin(Load, CheckPtr, PointerTaintOrigin)) {
                            ensureLevelSet(Load, ValueLevel, FunctionLevel);
                            errs() << "[SKIP] Load before taint origin, not tainting: "
                                   << getValueName(Load) << getDebugLoc(Load)
                                   << getFuncLevel(Load, ValueLevel, FunctionLevel) << "\n";
                            continue;
                        }

                        // Taint the load
                        ensureLevelSet(Load, ValueLevel, FunctionLevel);

                        if (isStructField) {
                            errs() << "[LOAD] Tainted load from tracked pointer (struct field): "
                                   << getValueName(Load) << " (base: " << getValueName(TaintedBasePtr) << ") "
                                   << getDebugLoc(Load) << getFuncLevel(Load, ValueLevel, FunctionLevel) << "\n";
                        } else {
                            errs() << "[LOAD] Tainted load from tracked pointer: "
                                   << getValueName(Load) << " (" << *Ptr << ") "
                                   << getDebugLoc(Load) << getFuncLevel(Load, ValueLevel, FunctionLevel) << "\n";
                        }

                        TaintedValues.insert(Load);
                        Worklist.push_back(Load);
                        changed = true;
                    }
                }
            }
        }

        return changed;
    }

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {

        SmallVector<Value*, 64> Worklist;
        DenseSet<Value*> TaintedValues;
        DenseSet<Value*> TaintedPointers;  // Track pointers that hold tainted values
        DenseSet<Instruction*> KilledStores;  // Track stores that kill taint (overwrite with non-tainted value)
        DenseSet<Function*> FunctionsReturningTaint;  // Track functions that return tainted values

        // Map from pointer to the instruction that caused it to be tainted (for execution order checking)
        DenseMap<Value*, Instruction*> PointerTaintOrigin;

        // Map from Value to its interprocedural level (0 = source function, +N = N levels up, -N = N levels down)
        DenseMap<Value*, int> ValueLevel;

        // Map from Function to its interprocedural level
        DenseMap<Function*, int> FunctionLevel;

        // Map from Function to set of parameter indices that receive tainted values via pointer stores
        DenseMap<Function*, DenseSet<unsigned>> FunctionsTaintingPointerParams;

        // Map from Function to map of parameter index to struct field indices accessed
        DenseMap<Function*, DenseMap<unsigned, SmallVector<int64_t, 4>>> FunctionParamFieldAccess;

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

                                        // Set the source function and instruction level to 0
                                        Function *SourceFunc = I.getFunction();
                                        if (SourceFunc) {
                                            FunctionLevel[SourceFunc] = 0;
                                        }
                                        ValueLevel[&I] = 0;

                                        errs() << "[SOURCE] Tainting: " << getValueName(&I) << getDebugLoc(&I) << getFuncLevel(&I, ValueLevel, FunctionLevel) << "\n";

                                        // Mark as part of data flow since it's in the worklist
                                        errs() << "[USE] Source instruction in data flow" << getDebugLoc(&I) << getFuncLevel(&I, ValueLevel, FunctionLevel) << "\n";

                                        // If this is a return instruction with the constant, report it
                                        if (ReturnInst *Ret = dyn_cast<ReturnInst>(&I)) {
                                            if (Ret->getReturnValue() == CI) {
                                                errs() << "[RETURN] Constant is returned directly"
                                                       << getDebugLoc(Ret) << getFuncLevel(Ret, ValueLevel, FunctionLevel) << "\n";
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
                                                   << getValueName(Ptr) << getDebugLoc(Store) << getFuncLevel(Store, ValueLevel, FunctionLevel) << "\n";

                                            // Check if storing to a global variable or pointer parameter (external effects)
                                            if (GlobalVariable *GV = dyn_cast<GlobalVariable>(Ptr)) {
                                                errs() << "[GLOBAL] Constant stored to global variable: "
                                                       << GV->getName() << getDebugLoc(Store) << getFuncLevel(Store, ValueLevel, FunctionLevel) << "\n";
                                            } else if (Argument *PtrParam = getPointerParameterOrigin(Store->getPointerOperand())) {
                                                errs() << "[POINTER PARAMETER] Constant stored through pointer parameter"
                                                       << getDebugLoc(Store) << getFuncLevel(Store, ValueLevel, FunctionLevel) << "\n";
                                                // Track this for upward interprocedural analysis
                                                Function *ContainingFunc = Store->getFunction();
                                                if (ContainingFunc) {
                                                    unsigned ParamIdx = PtrParam->getArgNo();
                                                    FunctionsTaintingPointerParams[ContainingFunc].insert(ParamIdx);
                                                    // Track which struct fields are accessed
                                                    SmallVector<int64_t, 4> fieldIndices = extractStructFieldIndices(Store->getPointerOperand(), nullptr, false);
                                                    if (!fieldIndices.empty()) {
                                                        DenseMap<unsigned, SmallVector<int64_t, 4>> &funcMap = FunctionParamFieldAccess[ContainingFunc];
                                                        SmallVector<int64_t, 4> &existingIndices = funcMap[ParamIdx];
                                                        for (int64_t idx : fieldIndices) {
                                                            if (std::find(existingIndices.begin(), existingIndices.end(), idx) == existingIndices.end()) {
                                                                existingIndices.push_back(idx);
                                                            }
                                                        }
                                                    }
                                                    if (Verbose) {
                                                        errs() << "  Tracking: Function " << ContainingFunc->getName()
                                                               << " taints parameter " << ParamIdx;
                                                        if (!fieldIndices.empty()) {
                                                            errs() << " fields [";
                                                            for (size_t i = 0; i < fieldIndices.size(); ++i) {
                                                                if (i > 0) errs() << ", ";
                                                                errs() << fieldIndices[i];
                                                            }
                                                            errs() << "]";
                                                        }
                                                        errs() << "\n";
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
                                                               << getDebugLoc(Call) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";

                                                        // In interproc mode, propagate taint to the parameter
                                                        if (InterprocMode && !Callee->isDeclaration()) {
                                                            if (ArgIdx < Callee->arg_size()) {
                                                                Argument *Param = Callee->getArg(ArgIdx);
                                                                if (TaintedValues.insert(Param).second) {
                                                                    // Downward interprocedural: level -= 1
                                                                    int currentLevel = getLevel(&I, ValueLevel, FunctionLevel);
                                                                    int newLevel = currentLevel - 1;
                                                                    ValueLevel[Param] = newLevel;
                                                                    FunctionLevel[Callee] = newLevel;

                                                                    Worklist.push_back(Param);
                                                                    errs() << "[INTERPROC] Propagating taint to parameter in "
                                                                           << Callee->getName() << ": "
                                                                           << getValueName(Param) << getDebugLoc(Call) << getFuncLevelForValue(Param, ValueLevel, FunctionLevel) << "\n";
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

                // Sort users for deterministic output
                SmallVector<User*, 16> SortedUsers = getSortedUsers(V);

                for (User *U : SortedUsers) {
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
                                    // Set level for Call instruction based on V
                                    if (!ValueLevel.count(Call)) {
                                        int currentLevel = getLevel(V, ValueLevel, FunctionLevel);
                                        ValueLevel[Call] = currentLevel;
                                    }

                                    // Report the call
                                    errs() << "  [CHILD FUNCTION] Tainted value used in call to "
                                           << Callee->getName() << " at argument " << argIdx
                                           << ": "
                                           << getValueName(Call)
                                           << getDebugLoc(Call) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";

                                    // In interproc mode, propagate taint to the parameter
                                    if (InterprocMode) {
                                        if (argIdx < Callee->arg_size()) {
                                            Argument *Param = Callee->getArg(argIdx);
                                            if (TaintedValues.insert(Param).second) {
                                                // Downward interprocedural: level -= 1
                                                int currentLevel = getLevel(V, ValueLevel, FunctionLevel);
                                                int newLevel = currentLevel - 1;
                                                ValueLevel[Param] = newLevel;
                                                FunctionLevel[Callee] = newLevel;

                                                Worklist.push_back(Param);
                                                errs() << "  [INTERPROC] Propagating taint to parameter in "
                                                       << Callee->getName() << ": "
                                                       << getValueName(Param) << getDebugLoc(Call) << getFuncLevelForValue(Param, ValueLevel, FunctionLevel) << "\n";
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
                                            // Sort entries for deterministic output
                                            SmallVector<std::pair<Value*, SmallVector<Function*, 4>>, 8> SortedEntries(
                                                FunctionPointerTargets.begin(), FunctionPointerTargets.end());
                                            llvm::sort(SortedEntries, [](const auto &A, const auto &B) {
                                                return std::less<Value*>()(A.first, B.first);
                                            });

                                            for (auto &Entry : SortedEntries) {
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
                                                    // Downward interprocedural: level -= 1
                                                    int currentLevel = getLevel(V, ValueLevel, FunctionLevel);
                                                    int newLevel = currentLevel - 1;
                                                    ValueLevel[Param] = newLevel;
                                                    FunctionLevel[Target] = newLevel;

                                                    Worklist.push_back(Param);
                                                    errs() << "    [INTERPROC] Propagating taint to parameter in "
                                                           << Target->getName() << ": "
                                                           << getValueName(Param) << getDebugLoc(Call) << getFuncLevelForValue(Param, ValueLevel, FunctionLevel) << "\n";
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
                            // Propagate level from V to UserInst
                            int currentLevel = getLevel(V, ValueLevel, FunctionLevel);
                            ValueLevel[UserInst] = currentLevel;

                            Worklist.push_back(UserInst);
                            errs() << "  [USE] Taint flows to: " << getValueName(UserInst) << getDebugLoc(UserInst) << getFuncLevel(UserInst, ValueLevel, FunctionLevel) << "\n";
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
                                    // Also check that this store happens AFTER the taint origin
                                    // If the taint origin exists and is in the same BB, only kill if after
                                    bool isValidKill = true;
                                    if (PointerTaintOrigin.count(Ptr)) {
                                        Instruction *TaintOrigin = PointerTaintOrigin[Ptr];
                                        if (Store->getParent() == TaintOrigin->getParent()) {
                                            // Same BB - check order
                                            bool foundOrigin = false;
                                            for (Instruction &CheckI : *Store->getParent()) {
                                                if (&CheckI == TaintOrigin) foundOrigin = true;
                                                if (&CheckI == Store && !foundOrigin) {
                                                    // Store is before taint origin - not a valid kill
                                                    isValidKill = false;
                                                    break;
                                                }
                                            }
                                        }
                                    }

                                    if (isValidKill) {
                                        KilledStores.insert(Store);
                                        errs() << "[KILL] Store overwrites tainted pointer with non-tainted value: "
                                               << getValueName(Store) /* << getDebugLoc(Store) */<< "\n";
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Scan for loads from newly tainted pointers
            // But skip loads that happen after a kill store
            SmallVector<Value*, 32> PointersToScan;
            // Sort TaintedPointers for deterministic output
            SmallVector<Value*, 32> SortedTaintedPointers(TaintedPointers.begin(), TaintedPointers.end());
            llvm::sort(SortedTaintedPointers, [](Value *A, Value *B) {
                return std::less<Value*>()(A, B);
            });
            for (Value *Ptr : SortedTaintedPointers) {
                if (!ScannedPointers.count(Ptr)) {
                    PointersToScan.push_back(Ptr);
                }
            }

            // Use helper function to scan loads with kill store tracking
            if (scanLoadsFromTaintedPointers(PointersToScan, M, TaintedValues,
                                             PointerTaintOrigin, ValueLevel, FunctionLevel,
                                             Worklist, &KilledStores)) {
                changed = true;
            }

            // Mark the pointers we just scanned
            for (Value *Ptr : PointersToScan) {
                ScannedPointers.insert(Ptr);
            }
        }

        // --- 5. Upward Interprocedural Taint Tracking (Callee -> Caller) - RECURSIVE ---
        if (UpwardInterprocMode && (!FunctionsReturningTaint.empty() || !FunctionsTaintingPointerParams.empty())) {
            if (Verbose) errs() << "=== Upward Interprocedural Tracking (Recursive) ===\n";

            // Keep track of scanned pointers across all recursive iterations
            DenseSet<Value*> UpwardScannedPointers;

            // Recursive loop: continue until no new parent functions are discovered
            bool discoveredNewFunctions = true;
            int recursionLevel = 0;

            while (discoveredNewFunctions) {
                discoveredNewFunctions = false;
                recursionLevel++;

                if (Verbose) errs() << "\n--- Upward Tracking Iteration " << recursionLevel << " ---\n";

                // Track sizes before this iteration to detect new discoveries
                size_t oldReturningSize = FunctionsReturningTaint.size();
                size_t oldPointerParamsSize = FunctionsTaintingPointerParams.size();

                // 5a. Find all call sites to functions that return tainted values
                // Sort FunctionsReturningTaint for deterministic output
                SmallVector<Function*, 16> SortedFunctionsReturningTaint(
                    FunctionsReturningTaint.begin(), FunctionsReturningTaint.end());
                llvm::sort(SortedFunctionsReturningTaint, [](Function *A, Function *B) {
                    return std::less<Function*>()(A, B);
                });
                for (Function *TaintedFunc : SortedFunctionsReturningTaint) {
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
                                            // Upward interprocedural: level += 1
                                            int calleeLevel = FunctionLevel.count(TaintedFunc) ? FunctionLevel[TaintedFunc] : 0;
                                            int newLevel = calleeLevel + 1;
                                            ValueLevel[Call] = newLevel;
                                            Function *CallerFunc = Call->getFunction();
                                            if (CallerFunc && !FunctionLevel.count(CallerFunc)) {
                                                FunctionLevel[CallerFunc] = newLevel;
                                            }

                                            errs() << "[UPWARD-INTERPROC] Call to " << TaintedFunc->getName()
                                                   << " returns tainted value" << getDebugLoc(Call) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";
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
                // Sort FunctionsTaintingPointerParams for deterministic output
                SmallVector<std::pair<Function*, DenseSet<unsigned>>, 16> SortedFunctionsTaintingPointerParams(
                    FunctionsTaintingPointerParams.begin(), FunctionsTaintingPointerParams.end());
                llvm::sort(SortedFunctionsTaintingPointerParams, [](const auto &A, const auto &B) {
                    return std::less<Function*>()(A.first, B.first);
                });
                for (auto &Entry : SortedFunctionsTaintingPointerParams) {
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
                                        // Sort TaintedParams for deterministic output
                                        SmallVector<unsigned, 8> SortedTaintedParams(TaintedParams.begin(), TaintedParams.end());
                                        llvm::sort(SortedTaintedParams);
                                        for (unsigned ParamIdx : SortedTaintedParams) {
                                            if (ParamIdx >= Call->arg_size()) continue;

                                            Value *ActualArg = Call->getArgOperand(ParamIdx);

                                            // CASE 1: Check if the argument is directly a pointer parameter (pass-through)
                                            // This handles cases like: grandparent(int *x) { parent(x); }
                                            // Use getPointerParameterOrigin to handle both direct parameters and loads from param allocas
                                            if (Argument *ArgParam = getPointerParameterOrigin(ActualArg)) {
                                                Function *CallerFunc = Call->getFunction();
                                                if (CallerFunc) {
                                                    unsigned CallerParamIdx = ArgParam->getArgNo();
                                                    if (FunctionsTaintingPointerParams[CallerFunc].insert(CallerParamIdx).second) {
                                                        discoveredNewFunctions = true;
                                                        // Upward interprocedural: level += 1
                                                        int calleeLevel = FunctionLevel.count(TaintedFunc) ? FunctionLevel[TaintedFunc] : 0;
                                                        int newLevel = calleeLevel + 1;
                                                        if (!FunctionLevel.count(CallerFunc)) {
                                                            FunctionLevel[CallerFunc] = newLevel;
                                                        }

                                                        errs() << "[POINTER PARAMETER] Call to " << TaintedFunc->getName()
                                                               << " passes through pointer parameter " << CallerParamIdx
                                                               << " of " << CallerFunc->getName()
                                                               << getDebugLoc(Call) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";
                                                        // errs() << "  [RECURSIVE] Discovered pass-through: Function "
                                                        //        << CallerFunc->getName() << " parameter " << CallerParamIdx << "\n";
                                                    }
                                                }
                                                continue; // Skip CASE 2 since this is a direct parameter pass-through
                                            }

                                            // CASE 2: Check if the argument is an address-of operation (alloca, GEP, etc.)
                                            // This handles cases like: grandparent(int *x) { int a; parent(&a); *x = a; }
                                            Value *PointedVar = nullptr;
                                            if (AllocaInst *AI = dyn_cast<AllocaInst>(ActualArg)) {
                                                PointedVar = AI;
                                            } else if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(ActualArg)) {
                                                PointedVar = GEP->getPointerOperand()->stripPointerCasts();
                                            }

                                            if (PointedVar) {
                                                if (TaintedPointers.insert(PointedVar).second) {
                                                    // Upward interprocedural: level += 1
                                                    int calleeLevel = FunctionLevel.count(TaintedFunc) ? FunctionLevel[TaintedFunc] : 0;
                                                    int newLevel = calleeLevel + 1;
                                                    Function *CallerFunc = Call->getFunction();
                                                    if (CallerFunc && !FunctionLevel.count(CallerFunc)) {
                                                        FunctionLevel[CallerFunc] = newLevel;
                                                    }

                                                    errs() << "[UPWARD-INTERPROC] Call to " << TaintedFunc->getName()
                                                           << " taints argument " << ParamIdx << " (local variable)"
                                                           << getDebugLoc(Call) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";
                                                    errs() << "  [STORE DESTINATION] Marking pointer as tainted via call: "
                                                           << getValueName(PointedVar) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";
                                                    PointerTaintOrigin[PointedVar] = Call;

                                                    // If this is a struct, also check for pointers stored in its fields
                                                    // This handles cases like: struct S {int *x;}; foo(&s); where foo taints through s->x
                                                    if (AllocaInst *AI = dyn_cast<AllocaInst>(PointedVar)) {
                                                        Type *AllocatedType = AI->getAllocatedType();
                                                        if (AllocatedType->isStructTy()) {
                                                            // Get the field indices that were accessed in the callee
                                                            SmallVector<int64_t, 4> accessedFields;
                                                            auto funcIt = FunctionParamFieldAccess.find(TaintedFunc);
                                                            if (funcIt != FunctionParamFieldAccess.end()) {
                                                                auto paramIt = funcIt->second.find(ParamIdx);
                                                                if (paramIt != funcIt->second.end()) {
                                                                    accessedFields = paramIt->second;
                                                                }
                                                            }

                                                            // Scan for GEPs on this struct and stores to those GEPs
                                                            for (User *U : AI->users()) {
                                                                if (GetElementPtrInst *GEP = dyn_cast<GetElementPtrInst>(U)) {
                                                                    // Extract the field index from this GEP
                                                                    int64_t fieldIdx = -1;
                                                                    if (GEP->getNumIndices() >= 2) {
                                                                        auto IdxIter = GEP->idx_begin();
                                                                        std::advance(IdxIter, GEP->getNumIndices() - 1);
                                                                        if (ConstantInt *CI = dyn_cast<ConstantInt>(&**IdxIter)) {
                                                                            fieldIdx = CI->getSExtValue();
                                                                        }
                                                                    }

                                                                    // Only process if this field was accessed (or if we don't have field info)
                                                                    if (accessedFields.empty() ||
                                                                        std::find(accessedFields.begin(), accessedFields.end(), fieldIdx) != accessedFields.end()) {
                                                                        // Check for stores to this GEP
                                                                        for (User *GU : GEP->users()) {
                                                                            if (StoreInst *SI = dyn_cast<StoreInst>(GU)) {
                                                                                if (SI->getPointerOperand() == GEP) {
                                                                                    Value *StoredVal = SI->getValueOperand()->stripPointerCasts();
                                                                                    // If we're storing a pointer/alloca, mark it as tainted
                                                                                    if (StoredVal->getType()->isPointerTy()) {
                                                                                        if (AllocaInst *StoredAlloca = dyn_cast<AllocaInst>(StoredVal)) {
                                                                                            if (TaintedPointers.insert(StoredAlloca).second) {
                                                                                                errs() << "  [UPWARD-INTERPROC] Marking struct field " << fieldIdx
                                                                                                       << " target as tainted: "
                                                                                                       << getValueName(StoredAlloca) << getFuncLevel(Call, ValueLevel, FunctionLevel) << "\n";
                                                                                                PointerTaintOrigin[StoredAlloca] = Call;
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
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
                // Loop: process worklist, then scan for loads, repeat until fixed point
                while (true) {
                    // Process worklist items
                    while (!Worklist.empty()) {
                        Value *V = Worklist.back();
                        Worklist.pop_back();

                        if (Verbose) errs() << "[USE] Processing uses of: " << getValueName(V) << "\n";

                        bool hasUses = false;
                        // Sort users for deterministic output
                        SmallVector<User*, 16> SortedUsersUpward = getSortedUsers(V);
                        for (User *U : SortedUsersUpward) {
                            Instruction *UserInst = dyn_cast<Instruction>(U);
                            if (!UserInst) continue;

                            if (TaintedValues.count(UserInst)) {
                                if (Verbose) errs() << "  [SKIP] Already tainted: " << getValueName(UserInst) << "\n";
                                continue;
                            }

                            hasUses = true;

                            // Propagate level from V to UserInst
                            int currentLevel = getLevel(V, ValueLevel, FunctionLevel);
                            ValueLevel[UserInst] = currentLevel;

                            errs() << "  [USE] Taint flows to: " << getValueName(UserInst) << getDebugLoc(UserInst) << getFuncLevel(UserInst, ValueLevel, FunctionLevel) << "\n";
                            TaintedValues.insert(UserInst);

                            // Handle store instructions - mark destination pointer as tainted
                            if (StoreInst *Store = dyn_cast<StoreInst>(UserInst)) {
                                if (processStoreForTaint(Store, V, TaintedPointers, PointerTaintOrigin,
                                                        FunctionsTaintingPointerParams, FunctionParamFieldAccess,
                                                        ValueLevel, FunctionLevel)) {
                                    discoveredNewFunctions = true;
                                }
                            }

                            // Handle return instructions - track for next recursion
                            if (ReturnInst *Ret = dyn_cast<ReturnInst>(UserInst)) {
                                if (Ret->getReturnValue() == V) {
                                    errs() << "  [RETURN] Tainted value is returned"
                                           << getDebugLoc(Ret) << getFuncLevel(Ret, ValueLevel, FunctionLevel) << "\n";
                                    Function *ContainingFunc = Ret->getFunction();
                                    if (ContainingFunc && FunctionsReturningTaint.insert(ContainingFunc).second) {
                                        discoveredNewFunctions = true;
                                        // errs() << "  [RECURSIVE] Discovered new function returning taint: "
                                        //        << ContainingFunc->getName() << "\n";
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
                    SmallVector<Value*, 32> PointersToScan;
                    // Sort TaintedPointers for deterministic output
                    SmallVector<Value*, 32> SortedTaintedPointersUpward(TaintedPointers.begin(), TaintedPointers.end());
                    llvm::sort(SortedTaintedPointersUpward, [](Value *A, Value *B) {
                        return std::less<Value*>()(A, B);
                    });
                    for (Value *Ptr : SortedTaintedPointersUpward) {
                        if (!UpwardScannedPointers.count(Ptr)) {
                            PointersToScan.push_back(Ptr);
                        }
                    }

                    if (PointersToScan.empty()) break;  // Fixed point reached

                    // Use helper function to scan loads (no kill store tracking in upward mode)
                    scanLoadsFromTaintedPointers(PointersToScan, M, TaintedValues,
                                                 PointerTaintOrigin, ValueLevel, FunctionLevel,
                                                 Worklist, nullptr);

                    for (Value *Ptr : PointersToScan) {
                        UpwardScannedPointers.insert(Ptr);
                    }
                }

                // Check if we discovered new functions in this iteration
                size_t newReturningSize = FunctionsReturningTaint.size();
                size_t newPointerParamsSize = FunctionsTaintingPointerParams.size();

                if (newReturningSize > oldReturningSize || newPointerParamsSize > oldPointerParamsSize) {
                    discoveredNewFunctions = true;
                    // errs() << "[RECURSIVE ITER " << recursionLevel << "] Discovered "
                    //        << (newReturningSize - oldReturningSize) << " new functions returning taint, "
                    //        << (newPointerParamsSize - oldPointerParamsSize) << " new functions tainting pointer params\n";
                } else {
                    // errs() << "[RECURSIVE ITER " << recursionLevel << "] No new parent functions discovered. "
                    //        << "Recursive tracking complete.\n";
                }
            }

            if (Verbose) errs() << "\n";
        }

        // --- Find the largest L value and the earliest/latest instruction with that L ---
        int maxLevel = INT_MIN;
        Instruction *earliestInst = nullptr;
        Instruction *latestInst = nullptr;

        // Find the maximum level (only considering actually tainted instructions, not skipped/killed ones)
        for (auto &Entry : ValueLevel) {
            Value *V = Entry.first;
            // Only consider values that are actually in TaintedValues (not skipped or killed)
            if (!TaintedValues.count(V)) continue;

            if (Entry.second > maxLevel) {
                maxLevel = Entry.second;
            }
        }

        if (maxLevel > INT_MIN) {
            // Collect all instructions with the maximum level
            SmallVector<Instruction*, 16> MaxLevelInstructions;
            for (auto &Entry : ValueLevel) {
                Value *V = Entry.first;
                // Only consider values that are actually in TaintedValues (not skipped or killed)
                if (!TaintedValues.count(V)) continue;

                if (Entry.second == maxLevel) {
                    if (Instruction *I = dyn_cast<Instruction>(V)) {
                        MaxLevelInstructions.push_back(I);
                    }
                }
            }

            // Find earliest and latest by iterating through the module in order
            // The first and last occurrences in program order
            if (!MaxLevelInstructions.empty()) {
                // Sort by pointer address to get deterministic ordering
                // Then scan module to find first and last in actual program order
                for (Function &F : M) {
                    if (F.isDeclaration()) continue;
                    for (BasicBlock &BB : F) {
                        for (Instruction &I : BB) {
                            // Check if this instruction is in our max level set
                            for (Instruction *MaxI : MaxLevelInstructions) {
                                if (&I == MaxI) {
                                    if (!earliestInst) {
                                        earliestInst = &I;
                                    }
                                    latestInst = &I;
                                }
                            }
                        }
                    }
                }

                errs() << "\n=== Maximum Level Statistics ===\n";
                errs() << "Largest L value: " << maxLevel << "\n";
                errs() << "Number of instructions with L=" << maxLevel << ": " << MaxLevelInstructions.size() << "\n";

                if (earliestInst) {
                    errs() << "\nEarliest instruction with L=" << maxLevel << ":\n";
                    errs() << "  " << getValueName(earliestInst) << getDebugLoc(earliestInst) << getFuncLevel(earliestInst, ValueLevel, FunctionLevel) << "\n";
                }

                if (latestInst && latestInst != earliestInst) {
                    errs() << "\nLatest instruction with L=" << maxLevel << ":\n";
                    errs() << "  " << getValueName(latestInst) << getDebugLoc(latestInst) << getFuncLevel(latestInst, ValueLevel, FunctionLevel) << "\n";
                } else if (latestInst == earliestInst) {
                    errs() << "\n(Earliest and latest are the same instruction)\n";
                }
            }
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
