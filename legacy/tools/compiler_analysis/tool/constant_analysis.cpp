// Credit: ChatGPT, FIXME more careful review is needed before serious use

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Basic/LangOptions.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Basic/SourceManager.h"
#include "clang/AST/Expr.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/ADT/SmallString.h"

using namespace llvm;
using namespace clang;
using namespace clang::tooling;

enum Pattern {
  AssignMacroConst,
  AssignIntegerLiteral
};

// /* FIXME more comprehensive blacklist */
// /* This is not in use. Let's be complete in this tool's output and come
//    up with heuristics in later stages */
// const std::unordered_set<std::string> ExcludedMacros = {
//   "true",
//   "false",
//   "NULL",
//   "AF_INET",
//   "AF_UNIX",
//   "AF_INET6",
//   "EINVAL",
//   "ENOMEM"
// };

//
// Command line options and help messages
//

static cl::OptionCategory ToolCategory("Constant analysis options");
static cl::extrahelp CommonHelp(CommonOptionsParser::HelpMessage);

static cl::opt<Pattern> Mode(
    "mode", cl::desc("The code pattern to find:"),
    cl::values(clEnumValN(Pattern::AssignMacroConst, "macro-const",
                          "Find assignments from macro constants"),
               clEnumValN(Pattern::AssignIntegerLiteral, "int-literal",
                          "Find assignments from integer literals")),
    cl::init(AssignMacroConst),
    cl::cat(ToolCategory)
);

//
// Helper functions for analyzing a single macro
//

std::string getExprSource(const Expr *E, const SourceManager &SM,
                          const LangOptions &LangOpts) {
  SourceRange Range = E->getSourceRange();
  CharSourceRange CharRange = CharSourceRange::getTokenRange(Range);
  StringRef Text = Lexer::getSourceText(CharRange, SM, LangOpts);
  return Text.str();
}

std::string getExpandedExpr(const Expr *E, const ASTContext &Ctx) {
  std::string S;
  raw_string_ostream OS(S);
  E->printPretty(OS, nullptr, PrintingPolicy(Ctx.getLangOpts()));
  return OS.str();
}

// FIXME Not passing simple tests
std::string getImmediateMacroName(SourceLocation Loc,
                                  const SourceManager &SM,
                                  const LangOptions &LangOpts) {
  if (Loc.isMacroID()) {
    StringRef Name = Lexer::getImmediateMacroName(Loc, SM, LangOpts);
    if (!Name.empty())
      return Name.str();
  }
  return "<not-a-macro>";
}

// FIXME Not passing simple tests
std::string getTopLevelMacroName(SourceLocation Loc,
                                 const SourceManager &SM,
                                 const LangOptions &LangOpts) {
  while (Loc.isMacroID()) {
    SourceLocation Immediate = SM.getImmediateMacroCallerLoc(Loc);
    if (!Immediate.isMacroID())
      break;
    Loc = Immediate;
  }
  return Lexer::getImmediateMacroName(Loc, SM, LangOpts).str();
}

// FIXME
// -42 => -
// (42) => (
std::string getExpandedExpr2(SourceLocation Loc, const SourceManager &SM,
                             const LangOptions &LangOpts) {
  SourceLocation SpellingLoc = SM.getSpellingLoc(Loc);
  Token Tok;
  if (!Lexer::getRawToken(SpellingLoc, Tok, SM, LangOpts, true)) {
    std::string MacroSpelling;
    raw_string_ostream OS(MacroSpelling);
    OS << Lexer::getSpelling(Tok, SM, LangOpts);
    return OS.str();
  }
  return "<unknown>";
}

class MyVisitor : public RecursiveASTVisitor<MyVisitor> {
public:
  explicit MyVisitor(ASTContext *Context) : Context(Context), CurrentFunction(nullptr) {}

  bool TraverseFunctionDecl(FunctionDecl *FD) {
    FunctionDecl *OldFD = CurrentFunction;
    CurrentFunction = FD;
    bool Ret = RecursiveASTVisitor<MyVisitor>::TraverseFunctionDecl(FD);
    CurrentFunction = OldFD;
    return Ret;
  }

  bool VisitBinaryOperator(BinaryOperator *BO) {
    if (!BO->isAssignmentOp())
      return true;

    Expr *RHS = BO->getRHS()->IgnoreImpCasts();
    const SourceManager &SM = Context->getSourceManager();
    SourceLocation SL = RHS->getExprLoc();

    // FIXME do not go further into included headers for now where statements
    // can also exist, e.g. inline, static functions
    if (!SM.isInMainFile(SL))
      return true;

    std::string FunctionNameStr = "<global>";
    if (CurrentFunction) {
      FunctionNameStr = CurrentFunction->getNameAsString();
    }

    //
    // Pattern matching
    //

    if (Mode == Pattern::AssignMacroConst) {
      if ((SM.isMacroBodyExpansion(SL) || SM.isMacroArgExpansion(SL)) &&
          RHS->isEvaluatable(*Context)) {

        std::string RHSSource = getExprSource(RHS, SM, Context->getLangOpts());
        std::string RHSExpanded = getExpandedExpr(RHS, *Context);
        std::string ImmediateMacroName = getImmediateMacroName(SL, SM, Context->getLangOpts());
        std::string TopMacroName = getTopLevelMacroName(SL, SM, Context->getLangOpts());
        std::string RHSExpanded2 = getExpandedExpr2(SL, SM, Context->getLangOpts());

        // if (ExcludedMacros.count(ImmediateMacroName))
        //   return true;

        Expr *LHS = BO->getLHS()->IgnoreImpCasts();
        std::string LHSStr;
        raw_string_ostream LS(LHSStr);
        LHS->printPretty(LS, nullptr, PrintingPolicy(Context->getLangOpts()));
        LS.flush();

        errs() << "FINDME" << ","
               << FunctionNameStr << ","
               << LHSStr << ","
               << "RHSSource=" << RHSSource << ","
               << "TopMacroName=" << TopMacroName << ","
               << "ImmediateMacroName=" << ImmediateMacroName << ","
               << "RHSExpanded=" << RHSExpanded << ","
               << "RHSExpanded2 = " << RHSExpanded2 << ","
               << SL.printToString(SM) << "\n";

        RHS->dump();
      }
    } else if (Mode == Pattern::AssignIntegerLiteral) {
      // Find positive integer literals
      if (auto *IL =
              dyn_cast<clang::IntegerLiteral>(RHS->IgnoreParenImpCasts())) {
        Expr *LHS = BO->getLHS()->IgnoreImpCasts();
        std::string LHSStr;
        raw_string_ostream LS(LHSStr);
        LHS->printPretty(LS, nullptr, PrintingPolicy(Context->getLangOpts()));
        LS.flush();

        SmallString<16> RHSSmallStr;
        IL->getValue().toString(RHSSmallStr, 10, true);
        std::string RHSStr(RHSSmallStr.c_str());

        std::string MacroNameStr = "<not-a-macro>";
        if (SL.isMacroID()) {
          MacroNameStr = getImmediateMacroName(SL, SM, Context->getLangOpts());
        }

        errs() << "FINDME_INT"
               << "," << FunctionNameStr << "," << LHSStr << "," << RHSStr
               << "," << MacroNameStr << "," << SL.printToString(SM) << "\n";

        RHS->dump();
        return true;
      }

      // Find negative integer literals
      if (auto *UO =
              dyn_cast<clang::UnaryOperator>(RHS->IgnoreParenImpCasts())) {
        if (UO->getOpcode() != UO_Minus)
          return true;
        if (auto *IL = dyn_cast<clang::IntegerLiteral>(
                UO->getSubExpr()->IgnoreParenImpCasts())) {
          Expr *LHS = BO->getLHS()->IgnoreImpCasts();
          std::string LHSStr;
          raw_string_ostream LS(LHSStr);
          LHS->printPretty(LS, nullptr,
                           PrintingPolicy(Context->getLangOpts()));
          LS.flush();

          SmallString<16> RHSSmallStr;
          IL->getValue().toString(RHSSmallStr, 10, true);
          std::string RHSStr(RHSSmallStr.c_str());
          RHSStr = "-" + RHSStr;

          std::string MacroNameStr = "<not-a-macro>";
          if (SL.isMacroID()) {
            MacroNameStr =
                getImmediateMacroName(SL, SM, Context->getLangOpts());
          }

          errs() << "FINDME_INT"
                 << "," << FunctionNameStr << "," << LHSStr << "," << RHSStr
                 << "," << MacroNameStr << "," << SL.printToString(SM) << "\n";

          RHS->dump();
        }
      }
    }

    return true;
  }

private:
  ASTContext *Context;
  FunctionDecl *CurrentFunction;
};

class MyConsumer : public ASTConsumer {
public:
  explicit MyConsumer(ASTContext *Context) : Visitor(Context) {}

  void HandleTranslationUnit(ASTContext &Context) override {
    Visitor.TraverseDecl(Context.getTranslationUnitDecl());
  }

private:
  MyVisitor Visitor;
};

class MyFrontendAction : public ASTFrontendAction {
public:
  std::unique_ptr<ASTConsumer> CreateASTConsumer(
      CompilerInstance &CI, StringRef) override {
    return std::make_unique<MyConsumer>(&CI.getASTContext());
  }
};

int main(int argc, const char **argv) {
  auto ExpectedParser = CommonOptionsParser::create(argc, argv, ToolCategory);
  if (!ExpectedParser) {
    errs() << "Failed to create CommonOptionsParser: "
           << toString(ExpectedParser.takeError()) << "\n";
    return 1;
  }

  CommonOptionsParser &OptionsParser = ExpectedParser.get();
  ClangTool Tool(OptionsParser.getCompilations(),
                 OptionsParser.getSourcePathList());
  return Tool.run(newFrontendActionFactory<MyFrontendAction>().get());
}
