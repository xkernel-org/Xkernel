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
    uint64_t ConstantToTrack;
    bool Verbose;

    // Constructor with parameters
    TaintTrackerPass(std::string FuncName, std::string Opcode, uint64_t Constant, bool Debug)
        : FunctionName(std::move(FuncName)), TargetOpcode(std::move(Opcode)),
          ConstantToTrack(Constant), Verbose(Debug) {}

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

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {

        SmallVector<Value*, 64> Worklist;
        DenseSet<Value*> TaintedValues;
        DenseSet<Value*> TaintedPointers;  // Track pointers that hold tainted values
        DenseSet<Instruction*> KilledStores;  // Track stores that kill taint (overwrite with non-tainted value)

        // --- 1. Seed the Worklist ---
        // Find the starting point based on function name, opcode, and constant value
        errs() << "=== Taint Tracker Configuration ===\n";
        errs() << "Function: " << FunctionName << "\n";
        errs() << "Opcode: " << TargetOpcode << "\n";
        errs() << "Constant: " << ConstantToTrack << "\n";
        errs() << "Verbose: " << (Verbose ? "ON" : "OFF") << "\n\n";

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
                                if (CI->getZExtValue() == ConstantToTrack) {
                                    if (TaintedValues.insert(&I).second) {
                                        Worklist.push_back(&I);
                                        errs() << "[SOURCE] Tainting: " << I << getDebugLoc(&I) << "\n";

                                        // If this is a return instruction with the constant, report it
                                        if (ReturnInst *Ret = dyn_cast<ReturnInst>(&I)) {
                                            if (Ret->getReturnValue() == CI) {
                                                errs() << "[RETURN] Constant is returned directly"
                                                       << getDebugLoc(Ret) << "\n";
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
                                            } else if (Argument *Arg = dyn_cast<Argument>(Ptr)) {
                                                if (Arg->getType()->isPointerTy()) {
                                                    errs() << "[POINTER PARAMETER] Constant stored to pointer parameter: "
                                                           << Arg->getName() << getDebugLoc(Store) << "\n";
                                                }
                                            } else {
                                                // Local variable - mark pointer as tainted for propagation
                                                if (TaintedPointers.insert(Ptr).second) {
                                                    // Already printed STORE DESTINATION above
                                                }
                                            }
                                        }

                                        // If this is a call instruction with the constant as an argument,
                                        // report it but don't track into the callee
                                        if (CallInst *Call = dyn_cast<CallInst>(&I)) {
                                            Function *Callee = Call->getCalledFunction();
                                            if (Callee) {
                                                // Find which argument position has the constant
                                                for (unsigned ArgIdx = 0; ArgIdx < Call->arg_size(); ++ArgIdx) {
                                                    if (Call->getArgOperand(ArgIdx) == CI) {
                                                        // Report for both internal and external functions
                                                        errs() << "[CHILD FUNCTION] Constant used in call to "
                                                               << Callee->getName() << " at argument " << ArgIdx
                                                               << getDebugLoc(Call) << "\n";
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
                                    goto found;
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

                        // --- Check for Sinks (Stop at function calls) ---
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
                                    // Report but don't propagate into callee
                                    errs() << "  [CHILD FUNCTION] Tainted value used in call to "
                                           << Callee->getName() << " at argument " << argIdx
                                           << getDebugLoc(Call) << "\n";
                                } else {
                                    errs() << "  [EXTERNAL CALL] Tainted value used in external/indirect call"
                                           << getDebugLoc(Call) << "\n";
                                }
                                // Don't continue - don't propagate the call further
                                continue;
                            }
                        }
                        if (ReturnInst *Ret = dyn_cast<ReturnInst>(UserInst)) {
                            if (Ret->getReturnValue() == V) {
                                errs() << "  [RETURN] Stop: Tainted value is returned: "
                                       << getValueName(Ret) << getDebugLoc(Ret) << "\n";
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
                                if (Argument *Arg = dyn_cast<Argument>(Ptr)) {
                                    if (Arg->getType()->isPointerTy()) {
                                        errs() << "  [POINTER PARAMETER] Tainted value stored to pointer parameter: "
                                               << Arg->getName() << getDebugLoc(Store) << "\n";
                                        continue;
                                    }
                                }
                                // For local variables, mark the pointer as tainted
                                // This allows us to track through variable assignments
                                if (TaintedPointers.insert(Ptr).second) {
                                    errs() << "  [STORE DESTINATION] Marking pointer as tainted: "
                                           << getValueName(Ptr) << getDebugLoc(Store) << "\n";
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
                    // Parse: taint-tracker<function_name;opcode;constant_value;debug>
                    if (Name.consume_front("taint-tracker")) {
                        std::string FunctionName = "gss_fill_context";  // default
                        std::string Opcode = "";  // default (empty means all opcodes)
                        uint64_t Constant = 3600;  // default
                        bool Debug = false;  // default

                        if (Name.consume_front("<") && Name.consume_back(">")) {
                            // Parse parameters separated by semicolons
                            SmallVector<StringRef, 4> Params;
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
                        }

                        MPM.addPass(TaintTrackerPass(FunctionName, Opcode, Constant, Debug));
                        return true;
                    }
                    return false;
                });
        }
    };
}
