#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Constants.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/DenseSet.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

struct TaintTrackerPass : public PassInfoMixin<TaintTrackerPass> {

    // --- Configuration ---
    // The constant value we are looking for.
    const uint64_t CONSTANT_TO_TRACK = 3600;
    // ---

    // Helper to print a value (like an instruction or argument)
    std::string getValueName(Value *V) {
        if (!V) return "N/A";
        std::string s;
        raw_string_ostream os(s);
        V->print(os);
        return os.str();
    }

    // The main entry point for your analysis
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
        errs() << "=== Running TaintTrackerPass ===\n";
        errs() << "Tainting all uses of constant: " << CONSTANT_TO_TRACK << "\n\n";

        // A worklist of tainted values to process
        SmallVector<Value*, 64> Worklist;

        // A set of all values we've already tainted (to avoid cycles)
        DenseSet<Value*> TaintedValues;

        // --- 1. Seed the Worklist ---
        // Find all instructions that use our constant
        for (Function &F : M) {
            for (BasicBlock &BB : F) {
                for (Instruction &I : BB) {
                    // Check all operands of this instruction
                    for (Value *Op : I.operands()) {
                        // Is the operand a ConstantInt?
                        if (ConstantInt *CI = dyn_cast<ConstantInt>(Op)) {
                            // Does it have the value we're looking for?
                            if (CI->getZExtValue() == CONSTANT_TO_TRACK) {
                                // Found a source! The instruction 'I' is now tainted.
                                // We add 'I' (the result of the instruction) to the worklist.
                                if (TaintedValues.insert(&I).second) {
                                    Worklist.push_back(&I);
                                    errs() << "[SOURCE] Tainting: " << getValueName(&I) << "\n";
                                }
                                // No need to check other operands of this instruction
                                break;
                            }
                        }
                    }
                }
            }
        }

        errs() << "\n--- Starting Taint Propagation --- \n";

        // --- 2. Run the Worklist Algorithm ---
        while (!Worklist.empty()) {
            Value *V = Worklist.pop_back_val();
            errs() << "[PROP] Processing uses of: " << getValueName(V) << "\n";

            // V is tainted. Now find all *uses* of V.
            for (User *U : V->users()) {
                // 'U' is the instruction that *uses* our tainted value 'V'
                if (Instruction *UserInst = dyn_cast<Instruction>(U)) {

                    // --- 3. Check for Sinks (Stop Cases) ---

                    // Case 1: Used in a function call
                    if (CallInst *Call = dyn_cast<CallInst>(UserInst)) {
                        // Check if our tainted value V is one of the arguments
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
                            continue; // Stop propagating down this path
                        }
                    }

                    // Case 2: Used in a return
                    if (ReturnInst *Ret = dyn_cast<ReturnInst>(UserInst)) {
                        if (Ret->getReturnValue() == V) {
                            errs() << "  [SINK] Stop: Tainted value is returned: "
                                   << getValueName(Ret) << "\n";
                            continue; // Stop propagating
                        }
                    }

                    // Case 3 & 4: Used in a store (affects memory)
                    if (StoreInst *Store = dyn_cast<StoreInst>(UserInst)) {
                        // We only care if our tainted value is the *value being stored*,
                        // not the address.
                        if (Store->getValueOperand() == V) {
                            Value *Ptr = Store->getPointerOperand()->stripPointerCasts();

                            // Case 3.1: A global variable
                            if (isa<GlobalVariable>(Ptr)) {
                                errs() << "  [SINK] Stop: Tainted value stored in Global Variable: "
                                       << Ptr->getName() << "\n";
                                continue; // Stop propagating
                            }

                            // Case 3.2: A pointer parameter
                            if (Argument *Arg = dyn_cast<Argument>(Ptr)) {
                                if (Arg->getType()->isPointerTy()) {
                                    errs() << "  [SINK] Stop: Tainted value stored to Pointer Parameter: "
                                           << Arg->getName() << "\n";
                                    continue; // Stop propagating
                                }
                            }
                            // Note: A more complex check could use GetUnderlyingObject
                            // to find stores to GEPs of pointer args, but this is a good start.
                        }
                    }

                    // --- 4. Propagate Taint ---
                    // If this use is not a sink, then the *result* of this
                    // instruction is now tainted.
                    if (TaintedValues.insert(UserInst).second) {
                        Worklist.push_back(UserInst);
                        errs() << "  [FLOW] Taint flows to: " << getValueName(UserInst) << "\n";
                    }
                }
            }
        }

        errs() << "\n=== Taint Analysis Complete ===\n";
        return PreservedAnalyses::all();
    }
};

// --- Registration ---
// This is the boilerplate to register your pass with 'opt'.
extern "C" LLVM_ATTRIBUTE_WEAK
::llvm::PassPluginLibraryInfo llvmGetPassPluginInfo() {
  return {
    LLVM_PLUGIN_API_VERSION, "TaintTrackerPass", "v0.1",
    [](PassBuilder &PB) {
      PB.registerPipelineParsingCallback(
        [](StringRef Name, ModulePassManager &MPM,
           ArrayRef<PassBuilder::PipelineElement>) {
          if (Name == "taint-tracker") {
            MPM.addPass(TaintTrackerPass());
            return true;
          }
          return false;
        }
      );
    }
  };
}
