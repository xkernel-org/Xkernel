#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Constants.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/DenseSet.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

// New Pass Manager style - no inheritance needed
struct TaintTrackerPass : public PassInfoMixin<TaintTrackerPass> {

    // --- Configuration ---
    const uint64_t CONSTANT_TO_TRACK = 3600;
    // ---

    // Helper to print a value
    std::string getValueName(Value *V) {
        if (!V) return "N/A";
        std::string s;
        raw_string_ostream os(s);
        V->print(os);
        return os.str();
    }

    // The main entry point for New Pass Manager
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {
        errs() << "=== Running TaintTrackerPass (New PM) ===\n";
        errs() << "Tainting all uses of constant: " << CONSTANT_TO_TRACK << "\n\n";

        SmallVector<Value*, 64> Worklist;
        DenseSet<Value*> TaintedValues;

        // --- 1. Seed the Worklist ---
        // (This logic is identical to the NPM version)
        for (Function &F : M) {
            for (BasicBlock &BB : F) {
                for (Instruction &I : BB) {
                    for (Value *Op : I.operands()) {
                        if (ConstantInt *CI = dyn_cast<ConstantInt>(Op)) {
                            if (CI->getZExtValue() == CONSTANT_TO_TRACK) {
                                if (TaintedValues.insert(&I).second) {
                                    Worklist.push_back(&I);
                                    errs() << "[SOURCE] Tainting: " << getValueName(&I) << "\n";
                                }
                                break;
                            }
                        }
                    }
                }
            }
        }

        errs() << "\n--- Starting Taint Propagation --- \n";

        // --- 2. Run the Worklist Algorithm ---
        // (This logic is identical to the NPM version)
        while (!Worklist.empty()) {
            Value *V = Worklist.pop_back_val();
            errs() << "[PROP] Processing uses of: " << getValueName(V) << "\n";

            for (User *U : V->users()) {
                if (Instruction *UserInst = dyn_cast<Instruction>(U)) {

                    // --- 3. Check for Sinks (Stop Cases) ---
                    // (This logic is identical to the NPM version)
                    if (CallInst *Call = dyn_cast<CallInst>(UserInst)) {
                        bool isArg = false;
                        for (Value *Arg : Call->args()) {
                            if (Arg == V) {
                                isArg = true;
                                break;
                            }
                        }
                        if (isArg) {
                            errs() << "  [SINK] Stop: Tainted value used in function call: "
                                   << getValueName(Call) << "\n";
                            continue;
                        }
                    }
                    if (ReturnInst *Ret = dyn_cast<ReturnInst>(UserInst)) {
                        if (Ret->getReturnValue() == V) {
                            errs() << "  [SINK] Stop: Tainted value is returned: "
                                   << getValueName(Ret) << "\n";
                            continue;
                        }
                    }
                    if (StoreInst *Store = dyn_cast<StoreInst>(UserInst)) {
                        if (Store->getValueOperand() == V) {
                            Value *Ptr = Store->getPointerOperand()->stripPointerCasts();
                            if (isa<GlobalVariable>(Ptr)) {
                                errs() << "  [SINK] Stop: Tainted value stored in Global Variable: "
                                       << Ptr->getName() << "\n";
                                continue;
                            }
                            if (Argument *Arg = dyn_cast<Argument>(Ptr)) {
                                if (Arg->getType()->isPointerTy()) {
                                    errs() << "  [SINK] Stop: Tainted value stored to Pointer Parameter: "
                                           << Arg->getName() << "\n";
                                    continue;
                                }
                            }
                        }
                    }

                    // --- 4. Propagate Taint ---
                    // (This logic is identical to the NPM version)
                    if (TaintedValues.insert(UserInst).second) {
                        Worklist.push_back(UserInst);
                        errs() << "  [FLOW] Taint flows to: " << getValueName(UserInst) << "\n";
                    }
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
                    if (Name == "taint-tracker") {
                        MPM.addPass(TaintTrackerPass());
                        return true;
                    }
                    return false;
                });
        }
    };
}
