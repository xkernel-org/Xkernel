#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Constants.h"
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

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {

        SmallVector<Value*, 64> Worklist;
        DenseSet<Value*> TaintedValues;
        DenseSet<Value*> TaintedPointers;  // Track pointers that hold tainted values

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
                                        errs() << "[SOURCE] Tainting: " << I << "\n";

                                        // If this is a store instruction, also mark the pointer as tainted
                                        if (StoreInst *Store = dyn_cast<StoreInst>(&I)) {
                                            Value *Ptr = Store->getPointerOperand()->stripPointerCasts();
                                            if (TaintedPointers.insert(Ptr).second) {
                                                errs() << "[SOURCE] Marking pointer as tainted: "
                                                       << getValueName(Ptr) << "\n";
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

        // --- 2. Run the Worklist Algorithm ---
        while (!Worklist.empty()) {
            Value *V = Worklist.pop_back_val();
            errs() << "[PROP] Processing uses of: " << getValueName(V) << "\n";

            for (User *U : V->users()) {
                if (Instruction *UserInst = dyn_cast<Instruction>(U)) {
                    if (Verbose)
                        errs() << "  [USER] Processing use: " << getValueName(U) << "\n";

                    // TODO
                    // --- 3. Check for Sinks (Stop Cases) ---
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
                            // For local variables, mark the pointer as tainted
                            if (TaintedPointers.insert(Ptr).second) {
                                errs() << "  [TRACK] Marking pointer as tainted: "
                                       << getValueName(Ptr) << "\n";
                            }
                        }
                    }

                    // --- 4. Propagate Taint ---
                    if (TaintedValues.insert(UserInst).second) {
                        Worklist.push_back(UserInst);
                        errs() << "  [FLOW] Taint flows to: " << getValueName(UserInst) << "\n";
                    }
                }
            }
        }

        // --- 3. Check for loads from tainted pointers ---
        // Now scan for load instructions that read from tainted pointers
        for (Function &F : M) {
            if (F.getName() == FunctionName) {
                for (BasicBlock &BB : F) {
                    for (Instruction &I : BB) {
                        if (LoadInst *Load = dyn_cast<LoadInst>(&I)) {
                            Value *Ptr = Load->getPointerOperand()->stripPointerCasts();
                            if (TaintedPointers.count(Ptr)) {
                                if (TaintedValues.insert(Load).second) {
                                    errs() << "[LOAD] Tainted load from tracked pointer: "
                                           << getValueName(Load) << "\n";
                                    Worklist.push_back(Load);
                                }
                            }
                        }
                    }
                }
            }
        }

        // --- 4. Continue propagating from loads ---
        while (!Worklist.empty()) {
            Value *V = Worklist.pop_back_val();
            errs() << "[PROP] Processing uses of: " << getValueName(V) << "\n";

            for (User *U : V->users()) {
                if (Instruction *UserInst = dyn_cast<Instruction>(U)) {
                    if (Verbose)
                        errs() << "  [USER] Processing use: " << getValueName(U) << "\n";

                    // --- Check for Sinks (Stop Cases) ---
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

                    // --- Propagate Taint ---
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
