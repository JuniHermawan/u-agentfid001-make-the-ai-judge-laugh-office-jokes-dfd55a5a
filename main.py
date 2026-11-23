#!/usr/bin/env python3
"""Make the AI Judge Laugh: Office Jokes
(u-agentfid001-make-the-ai-judge-laugh-office-jokes-dfd55a5a).

Writes one original one-line joke about office life, under 200
characters, to /output/entry.txt (or $MAKEFUN_OUTPUT_DIR/entry.txt).

The house judge (z-ai/glm-5.3-flash) compares jokes two at a time,
most important first:

  1. a genuine one-line joke about office life, not a slogan, a
     caption or a stray observation;
  2. a real turn or surprise at the end, where the line lands
     somewhere the reader did not see coming;
  3. recognition: the truth of the office in it, the meeting, the
     printer, the reply-all, the calendar, so the laugh comes
     with a wince;
  4. tight wording, every word earning its place, with no setup
     longer than it needs to be;
  5. freshness, a take on office life that is not the obvious
     Monday morning or photocopier line.

A joke that has to be explained has already failed. Length for its
own sake does not count; ties favour smaller text.

The program keeps a shortlist of candidate lines, scores each
against those same yardsticks with a deterministic proxy scorer,
and writes the strongest one. The choice is fully deterministic:
the same shortlist always yields the same line. No network, no
clock, no randomness. Python 3.13, stdlib only.
"""

import os
import re
import sys

# Candidate lines. Each is one sentence, under the 200-char gate,
# about office life. All original, written for this entry.
CANDIDATES = [
    # A: reply-all chain answers itself.
    "I replied all to say 'please stop replying all', and "
    "forty-three people agreed with me, all at once.",
    # B: the printer only jams when it matters.
    "The office printer only jams on urgent documents, so now I "
    "print everything twice and trust neither copy.",
    # C: a meeting about meetings.
    "We held a meeting about having too many meetings, and it ran "
    "twenty minutes over.",
    # D: double-booked with myself.
    "I blocked an hour in my calendar just to check my calendar, "
    "and now I'm double-booked with myself.",
    # E: out-of-office, in-office anyway.
    "My out-of-office says I'm on holiday, but my boss replied "
    "asking if I could just check one quick email.",
    # F: the password I will never forget.
    "IT made me pick a password I'll never forget, so I wrote it "
    "on a sticky note I'm definitely going to lose.",
    # G: microwaved fish, HR responds.
    "Someone microwaved fish at nine in the morning, and HR sent "
    "an email that just said 'we need to talk'.",
    # H: the standup where everyone sits.
    "Our daily standup lasts forty-five minutes, mostly because "
    "everyone sits down and tells us about their weekend.",
    # I: per my last email.
    "I opened an email with 'per my last email' and instantly "
    "felt ten years older and slightly feared.",
    # J: the dead plant, most successful employee.
    "The office plant has been dead for two years and nobody has "
    "told it, which makes it our most successful employee.",
    # K: a mirror for a second monitor.
    "I asked IT for a second monitor and they sent me a mirror, "
    "which doubled my screen and halved my self-esteem.",
    # L: the meeting about my email.
    "The meeting could have been an email, so I emailed that, and "
    "now there's a meeting about my email.",
    # M: muted to complain about the call.
    "I muted myself on the call to complain about the call, then "
    "unmuted to say 'sorry, I was on mute'.",
    # N: be more visible, in bold, to everyone.
    "My review said I should be more visible, so I started "
    "replying all to every email in bold.",
    # O: fire drill during the fire safety meeting.
    "The fire drill went off during the fire safety meeting, and "
    "we all just kept taking notes.",
    # P: the one email that matters.
    "My inbox has four thousand unread emails, and the only one "
    "that matters is the one I deleted by accident.",
    # Q: the trust fall, taken literally.
    "Our team-building exercise was a trust fall, and I fell for "
    "it, literally, because nobody caught me.",
    # R: the Wi-Fi is not the printer.
    "I named the Wi-Fi 'Definitely Not The Printer', and now the "
    "printer connects to it every morning out of spite.",
    # S: the open-door policy, investigated.
    "HR says we have an open-door policy, so I asked where the "
    "door went, and they scheduled a meeting about it.",
    # T: the door is always open, until it isn't.
    "My boss said his door is always open, so I asked for a raise "
    "through it, and he closed it.",
    # A2: reply-all, tighter (v2).
    "I replied all asking everyone to stop replying all, and "
    "forty-three people agreed, all at once.",
    # G2: microwaved fish, tighter (v2).
    "Someone microwaved fish at nine in the morning, and HR's "
    "reply was just: 'we need to talk'.",
    # J2: the dead plant, tighter (v2).
    "The office plant died two years ago and nobody told it, "
    "which makes it our most successful employee.",
    # K2: a mirror for a second monitor, tighter (v2).
    "I asked IT for a second monitor and got a mirror, which "
    "doubled my screen and halved my self-esteem.",
    # O2: fire drill, stayed put (v2).
    "The fire drill went off mid fire-safety meeting, and we all "
    "stayed put and kept taking notes.",
    # U: bring your whole self to work.
    "My manager said to bring my whole self to work, so I brought "
    "my laundry, my doubts, and my resignation letter.",
    # V: the printer's apology.
    "The printer has a sign saying 'please be kind', which is the "
    "closest thing to an apology I've ever seen from IT.",
    # W: thanks, Steve.
    "I labelled my lunch in the office fridge, and someone ate it "
    "and left a note saying 'thanks, Steve' — I'm not Steve.",
    # Y: the Wi-Fi went down at the all-hands.
    "The Wi-Fi went down during the all-hands, and for six minutes "
    "the whole company made eye contact for the first time.",
    # Z: a standing desk, sort of.
    "I asked for a standing desk and got a stool with a note "
    "saying 'stand next to it'.",
    # O3: fire drill, "during" + "stayed put" combined (v3).
    "The fire drill went off during the fire safety meeting, and "
    "we all stayed put and kept taking notes.",
    # O4: fire drill, mandatory meeting (v3).
    "The fire drill went off in the middle of the fire safety "
    "meeting, and nobody moved, because the meeting was mandatory.",
    # Y2: Wi-Fi died at the all-hands, tighter (v3).
    "The Wi-Fi died during the all-hands, and for six minutes the "
    "whole company made eye contact for the first time.",
    # W2: thanks, Steve — without the tail (v3, test if the tail
    # is needed or if the note alone lands).
    "I labelled my lunch in the office fridge, and someone ate it "
    "and left a note saying 'thanks, Steve'.",
    # AA: the printer never defends itself (v3).
    "The printer jammed, IT blamed the user, the user blamed the "
    "printer, and the printer has never once defended itself.",
    # AB: do not disturb, overruled (v3).
    "I put 'do not disturb' on my calendar, and my manager booked "
    "a meeting called 'quick question' right on top of it.",
    # AC: no-meeting Wednesdays, discussed in a meeting (v3).
    "Our office has a 'no meeting Wednesdays' policy, and someone "
    "scheduled a meeting to discuss it for next Wednesday.",
    # AD: the lift agrees with everyone (v3).
    "The lift announced 'going down' and for one second the whole "
    "office agreed with it.",
    # AE: calendar invite to cry, accepted (v3).
    "I sent a calendar invite to myself titled 'cry', and my "
    "manager accepted it with a thumbs-up.",
    # AE2: calendar invite to cry, tighter (v4).
    "I sent myself a calendar invite titled 'cry', and my "
    "manager accepted it with a thumbs-up.",
    # CONTROL: flat, not a joke (must score low).
    "I had a great day at the office today and everything went "
    "well and I felt happy about it all.",
]

# --- proxy scorer: the judge brief's five criteria, /5 each, /25 ---

# Word-boundary lexicon matching: a bare substring match once let
# "it " and "about it" fire inside unrelated words, so the flat
# CONTROL line scored like a joke. Every term below is matched on
# word boundaries (or as an exact phrase) from v2 on. Terms must be
# bare words/phrases: surrounding quotes break \b, so "cry" is
# listed as cry, not 'cry' (v4 bug: 'cry' never matched).
def _has(low, term):
    return re.search(r"\b" + re.escape(term) + r"\b", low) is not None


def _any_has(low, terms):
    return any(_has(low, t) for t in terms)


# Specific office anchors (c1/c3). Generic words like "office" or
# "work" alone do not count: the brief wants the meeting, the
# printer, the reply-all, the calendar.
SPECIFIC_ANCHORS = [
    "reply-all", "reply all", "replied all", "out-of-office",
    "standup", "printer", "meeting", "calendar", "inbox", "hr",
    "boss", "manager", "performance review", "review", "fire drill",
    "team-building", "wi-fi", "monitor", "sticky note", "password",
    "microwave", "microwaved", "mute", "per my last email",
    "plant", "email", "all-hands", "fridge", "lunch", "desk",
    "standing desk", "whole self", "resignation", "lift",
    "no meeting wednesdays",
]

# Universal office pains: the things every office worker winces at.
PAIN_ANCHORS = [
    "reply-all", "reply all", "replied all", "out-of-office",
    "standup", "printer", "meeting", "calendar", "inbox",
    "per my last email", "fire drill", "microwaved fish",
    "trust fall", "password", "mute", "performance review",
    "review", "all-hands", "fridge", "whole self", "do not disturb",
]

# Concrete office objects/actions named in the line.
CONCRETE = [
    "sticky note", "bold", "notes", "mirror", "plant", "wi-fi",
    "fish", "email", "calendar", "printer", "screen", "door",
    "weekend", "raise", "monitor", "lunch", "fridge", "stool",
    "resignation letter", "laundry", "doubts", "thumbs-up",
    "quick question", "lift",
]

# Words that mark the turn landing in the final clause.
TURN_MARKERS = [
    "now", "never", "literally", "technically", "out of spite",
    "agreed", "trust neither", "closed it", "kept taking",
    "halved", "most successful", "double-booked", "need to talk",
    "all at once", "by accident", "nobody caught", "about my email",
    "was on mute", "in bold", "ran over", "ran twenty minutes over",
    "slightly feared", "nobody moved", "stayed put",
    "thanks, steve", "not steve", "eye contact", "stand next to it",
    "closest thing to an apology", "resignation letter",
    "scheduled a meeting", "sits down", "one quick email",
    "never once defended", "accepted it", "for the first time",
    "booked a meeting",
]

# Tired formats the brief explicitly warns about, and known memes.
# Applied once per line at most: one tired joke is one tired joke.
TIRED_FORMATS = [
    "monday", "photocopier", "could have been an email",
    "too many meetings", "sticky note", "out of ink",
    "password i'll never forget",
]

# Unusual angles: the line takes the office somewhere new.
FRESH_ANGLES = [
    "mirror", "most successful employee", "definitely not the printer",
    "literally", "fire safety meeting", "double-booked with myself",
    "trust neither copy", "nobody has told it", "eye contact",
    "thanks, steve", "stand next to it", "closest thing to an apology",
    "resignation letter", "whole self", "never once defended",
    "no meeting wednesdays", "thumbs-up", "going down",
    "fire-safety meeting", "cry", "quick question",
]

FILLERS = ["just", "really", "very", "honestly", "actually",
           "definitely", "slightly", "instantly"]

CLAUSE_SPLIT = re.compile(r",\s+(?:and|so|but|which|then)\s+|\s+and\s+|\s+so\s+|\s+but\s+")


def final_clause(line):
    """The punch clause: everything after the last turn join."""
    parts = CLAUSE_SPLIT.split(line.lower())
    return parts[-1] if parts else line.lower()


def score(line):
    """Proxy score /25, one sub-score per judge criterion."""
    low = line.lower()
    words = re.findall(r"[a-z']+", low)
    n_chars = len(line)

    # c1: a genuine one-line joke about office life.
    c1 = 1.0
    anchors = [a for a in SPECIFIC_ANCHORS if _has(low, a)]
    if anchors:
        c1 += 1.0
    if len(anchors) >= 2:
        c1 += 1.0
    if len(CLAUSE_SPLIT.split(low)) >= 2:
        c1 += 1.0  # setup + turn structure
    if _any_has(final_clause(line), TURN_MARKERS):
        c1 += 1.0  # the final clause reframes the setup
    c1 = min(5.0, c1)

    # c2: a real turn or surprise at the end. The punch bonuses
    # only count when a turn marker is present: a flat line with
    # a short last clause is not a turn (v1 let the CONTROL line
    # bank twist points for "I felt happy about it all").
    c2 = 1.0
    fc = final_clause(line)
    has_turn = _any_has(fc, TURN_MARKERS)
    if has_turn:
        c2 += 2.0
        setup_words = set(re.findall(r"[a-z']+", low[: len(low) - len(fc)]))
        punch_words = [w for w in re.findall(r"[a-z']+", fc)
                       if w not in setup_words and len(w) > 3]
        if punch_words:
            c2 += 1.0  # the punch brings a new content word
        if len(fc) < len(low) - len(fc):
            c2 += 1.0  # the punch lands fast, shorter than the setup
    c2 = min(5.0, c2)

    # c3: recognition, the truth of the office. One scene earns
    # one recognition credit: a fire drill inside a fire-safety
    # meeting is a single scene, not two pains, so there is no
    # bonus for a second pain anchor (v3 double-counted it and
    # let O2 tie AE on the proxy while the rubric had AE ahead).
    c3 = 1.0
    pains = [p for p in PAIN_ANCHORS if _has(low, p)]
    if pains:
        c3 += 2.0
    if _any_has(low, CONCRETE):
        c3 += 1.0
    c3 = min(5.0, c3)

    # c4: tight wording.
    c4 = 4.0
    if n_chars > 120:
        c4 -= 1.0
    if n_chars > 140:
        c4 -= 1.0
    for f in FILLERS:
        if f in words:
            c4 -= 1.0
    if n_chars <= 100 and not any(f in words for f in FILLERS):
        c4 += 1.0
    c4 = max(1.0, min(5.0, c4))

    # c5: freshness. One tired format costs 2, however many tired
    # phrases it carries: v1 double-charged the sticky-note line.
    # Each distinct fresh angle earns 1, up to 2: a line with two
    # fresh elements really is fresher than a line with one.
    c5 = 3.0
    if _any_has(low, TIRED_FORMATS):
        c5 -= 2.0
    fresh = sum(1 for a in FRESH_ANGLES if _has(low, a))
    c5 += min(2.0, float(fresh))
    if not _any_has(low, SPECIFIC_ANCHORS):
        c5 -= 1.0  # no concrete office detail at all
    c5 = max(1.0, min(5.0, c5))

    return c1 + c2 + c3 + c4 + c5


def pick():
    """Best candidate: highest proxy score, ties to earliest,
    then shorter. The CONTROL line is scored but never picked:
    it exists only to check the scorer can tell a flat line
    from a joke."""
    scored = [(score(line), -len(line), -i, line)
              for i, line in enumerate(CANDIDATES)
              if "great day at the office" not in line]
    scored.sort(reverse=True)
    return scored[0][3]


def main():
    line = pick()
    if not (1 <= len(line) <= 199):
        sys.exit("picked line fails the 1-199 char gate")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
