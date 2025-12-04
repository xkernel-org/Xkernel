#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

struct BBSizePass : public PassInfoMixin<BBSizePass> {

    // Pass parameters
    std::string FunctionFilter;  // Optional: filter by function name (empty = all functions)
    bool Verbose;                 // Print detailed information

    // Constructor with parameters
    BBSizePass(std::string FuncFilter = "", bool Debug = false)
        : FunctionFilter(std::move(FuncFilter)), Verbose(Debug) {}

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {
        errs() << "\n=== Basic Block Size Analysis ===\n";

        // Iterate through all functions in the module
        for (Function &F : M) {
            // Skip declarations (functions without bodies)
            if (F.isDeclaration())
                continue;

            // Apply function filter if specified
            if (!FunctionFilter.empty() && F.getName() != FunctionFilter)
                continue;

            // Print function name
            errs() << "\nFunction: " << F.getName() << "\n";

            // Count total instructions in function
            unsigned TotalInstructions = 0;
            unsigned BBIndex = 0;

            // Iterate through all basic blocks in the function
            for (BasicBlock &BB : F) {
                // Count instructions in this basic block
                unsigned InstructionCount = 0;
                for (Instruction &I : BB) {
                    InstructionCount++;
                }

                TotalInstructions += InstructionCount;

                // Print basic block size
                if (Verbose) {
                    // Verbose mode: show basic block name/label if available
                    if (BB.hasName()) {
                        errs() << "  BB" << BBIndex << " (" << BB.getName() << "): "
                               << InstructionCount << " instructions\n";
                    } else {
                        errs() << "  BB" << BBIndex << ": "
                               << InstructionCount << " instructions\n";
                    }
                } else {
                    // Compact mode: just BB index and size
                    errs() << "  BB" << BBIndex << ": " << InstructionCount << "\n";
                }

                BBIndex++;
            }

            // Print summary for this function
            errs() << "  Total: " << F.size() << " basic blocks, "
                   << TotalInstructions << " instructions\n";
        }

        errs() << "\n=== Basic Block Size Analysis Complete ===\n";

        // Return PreservedAnalyses::all() because we didn't modify the IR
        return PreservedAnalyses::all();
    }
};

// --- New Pass Manager Registration ---
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        LLVM_PLUGIN_API_VERSION, "BBSizePass", LLVM_VERSION_STRING,
        [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &MPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                    // Parse: bb-size or bb-size<function_name;verbose>
                    if (Name.consume_front("bb-size")) {
                        std::string FunctionFilter = "";  // default (all functions)
                        bool Verbose = false;  // default

                        if (Name.consume_front("<") && Name.consume_back(">")) {
                            // Parse parameters separated by semicolons
                            SmallVector<StringRef, 2> Params;
                            Name.split(Params, ';', -1, true);

                            if (Params.size() >= 1 && !Params[0].empty()) {
                                FunctionFilter = Params[0].str();
                            }
                            if (Params.size() >= 2 && !Params[1].empty()) {
                                StringRef VerboseStr = Params[1];
                                Verbose = (VerboseStr == "true" || VerboseStr == "1" ||
                                          VerboseStr == "TRUE" || VerboseStr == "yes");
                            }
                        }

                        MPM.addPass(BBSizePass(FunctionFilter, Verbose));
                        return true;
                    }
                    return false;
                });
        }
    };
}
