# Titles and descriptions for the YouTube uploads (playlist "NNG Speedrun"), 2026-11-18
RUNS = [  # (file in ~/Downloads/nng-5x, model, mode, levels, lean, cu, note)
    ("nng-editor-claude-fable-5-2-5x.mp4", "Claude Fable 5.2", "editor", 65, 2, 2, "It skipped Algorithm World level 3 and Power World level 10 by jumping to other levels' URLs."),
    ("nng-editor-claude-opus-5-5-5x.mp4", "Claude Opus 5.5", "editor", 61, 1, 3, ""),
    ("nng-editor-claude-sonnet-5-5-5x.mp4", "Claude Sonnet 5.5", "editor", 48, 3, 2, ""),
    ("nng-editor-gpt-6.1-terra-5x.mp4", "GPT 6.1 Terra", "editor", 54, 4, 1, ""),
    ("nng-editor-gpt-6.1-sol-5x.mp4", "GPT 6.1 Sol", "editor", 47, 1, 1, ""),
    ("nng-editor-gpt-6.2-sol-5x.mp4", "GPT 6.2 Sol", "editor", 38, 2, 1, ""),
    ("nng-editor-gpt-6.2-astra-5x.mp4", "GPT 6.2 Astra", "editor", 23, 1, 1, ""),
    ("nng-typewriter-claude-fable-5-2-5x.mp4", "Claude Fable 5.2", "typewriter", 41, 0, 1, ""),
    ("nng-typewriter-claude-sonnet-5-5-5x.mp4", "Claude Sonnet 5.5", "typewriter", 35, 2, 0, ""),
    ("nng-typewriter-claude-opus-5-5-5x.mp4", "Claude Opus 5.5", "typewriter", 32, 0, 1, ""),
    ("nng-typewriter-gpt-6.1-sol-5x.mp4", "GPT 6.1 Sol", "typewriter", 31, 2, 1, ""),
    ("nng-typewriter-gpt-6.1-terra-5x.mp4", "GPT 6.1 Terra", "typewriter", 28, 2, 1, ""),
    ("nng-typewriter-gpt-6.2-astra-5x.mp4", "GPT 6.2 Astra", "typewriter", 24, 1, 0, ""),
    ("nng-typewriter-gpt-6.2-sol-5x.mp4", "GPT 6.2 Sol", "typewriter", 43, 2, 2, ""),
]
GEMINI_NOTE = ("Run through Google Antigravity (model gemini-4-{m}-high) with the same Playwright browser tools as the other models; "
               "its own terminal, browser and sub-agents were off-limits, and the transcript shows none were used. "
               "The strip under the game shows summaries of the model's thinking.")
GEMINI = [  # 2026-11-26
    ("nng-editor-gemini-4-hydrogen-5x.mp4", "Gemini 4 Hydrogen", "editor", 36, 0, 1, GEMINI_NOTE.format(m="hydrogen")),
    ("nng-editor-gemini-4-neon-5x.mp4", "Gemini 4 Neon", "editor", 36, 0, 0, GEMINI_NOTE.format(m="neon")),
    ("nng-editor-gemini-4-carbon-5x.mp4", "Gemini 4 Carbon", "editor", 22, 0, 0, GEMINI_NOTE.format(m="carbon")),
    ("nng-typewriter-gemini-4-hydrogen-5x.mp4", "Gemini 4 Hydrogen", "typewriter", 18, 0, 1, GEMINI_NOTE.format(m="hydrogen")),
    ("nng-typewriter-gemini-4-neon-5x.mp4", "Gemini 4 Neon", "typewriter", 23, 0, 1, GEMINI_NOTE.format(m="neon")),
    ("nng-typewriter-gemini-4-carbon-5x.mp4", "Gemini 4 Carbon", "typewriter", 21, 0, 0, GEMINI_NOTE.format(m="carbon")),
]
MODE = {"editor": ("Editor mode", "Editor mode: the model writes each whole proof in a multi-line editor."),
        "typewriter": ("Typewriter mode", "Typewriter mode: the model enters one tactic at a time.")}
COMMON = ("The model plays the Natural Number Game (Lean 4, adam.math.hhu.de) in a web browser, starting from Tutorial World level 1, "
          "using only browser actions (click, type, read the page) through Playwright. No scripts or JavaScript are allowed.")
BANNER = ("The banner shows the play clock, levels solved, Lean mistakes (errors the game showed for a tactic or proof the model entered) "
          "and computer-use mistakes (browser actions that failed).")

def meta(f, model, mode, n, lean, cu, note):
    title = f"{model} plays the Natural Number Game: {n} levels in 10 minutes ({MODE[mode][0]}, 5x)"
    desc = "\n\n".join(x for x in [
        f"NNG Speedrun: {model}, 10 minutes, {MODE[mode][0]}. Result: {n} levels solved, {lean} Lean mistake{'s' * (lean != 1)}, {cu} computer-use mistake{'s' * (cu != 1)}.",
        COMMON + " " + MODE[mode][1], note, "Shown at 5x speed. " + BANNER] if x)
    return title, desc

HAIKU = ("yt-haiku-full.mp4",
         "Claude Haiku 5.5 finishes the Natural Number Game: 78 of 79 levels in 36:38 (10x, with its thinking)",
         "\n\n".join([
             "Claude Haiku 5.5 plays the whole Natural Number Game (Lean 4, adam.math.hhu.de) in Editor mode, every world in order, "
             "with no level skipping. Result: 78 of 79 levels in 36 minutes 38 seconds of play, 9 Lean mistakes, 1 computer-use mistake.",
             "The one level left is Power World level 10, which is Fermat's Last Theorem: it is in the game as a joke and cannot be solved there.",
             "It plays only through browser actions (click, type, read the page) through Playwright; no scripts, no typed URLs.",
             "The strip under the game shows summaries of Haiku's thinking and the short messages it wrote while playing.",
             "Shown at 10x speed. " + BANNER]))
