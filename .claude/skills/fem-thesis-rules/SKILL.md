---
name: fem-thesis-rules
description: Poznan University of Technology, Faculty of Engineering Management (FEM) rules for the engineering/diploma thesis, from the FEM Regulations edition 12 (in force from 2 October 2025) and the diploma seminar, plus an Overleaf-ready LaTeX template that implements them (latex/). Use when writing, restructuring, formatting or reviewing the GridMind thesis, its abstracts, title, APD/USOS topic card, bibliography, tables, figures and formulas, the LaTeX/Overleaf project, or the seminar/defence presentation. Also use for Turkish requests such as "tez yapısı", "tez formatı", "başlık nasıl olmalı", "kaynakça", "tablo kaynağı", "LaTeX şablonu", "Overleaf", "seminer sunumu", "giriş/sonuç bölümü", "sayfa sayısı", "savunma".
---

# FEM diploma thesis rules and LaTeX template

## 0. Sources and precedence

1. **FEM Regulations on the Completion of Diploma Theses and the Diploma Examination, edition 12, in force from 02.10.2025.** Binding. If the English translation and the Polish original differ, the Polish version prevails. Section numbers below (e.g. 6.4.1) refer to this document.
2. The official FEM title-page template (fem.put.poznan.pl → Student → templates of diploma documents).
3. Diploma seminar slides and notes (14 October 2026): secondary guidance. Where they differ from edition 12, follow edition 12 and say so.

Edition 10 (2023) is superseded. Changes in edition 12 that matter:
- headings are bold
- page numbers go on the outer edge
- only bold is allowed for emphasis
- table sources are left-aligned
- formulas also need a source
- the innovativeness/implementation section is now mandatory

## 1. Topic and APD topic card (appendix to edition 12)

- **Topic:** must relate to the field of study, refer to an engineering concept, project or process, and solve an engineering problem.
- **Title:** must show three things:
  - what is analysed or designed (*przedmiot badań*)
  - where, i.e. in which facility or system (*podmiot badań*)
  - the objective (optimisation, improvement, enhancement)
- **Subject/object wording:** the English translation calls the first "subject" and the second "object"; the seminar slides used the opposite words. Use the Polish terms, or the wording the supervisor uses, and keep it the same everywhere.
- No full stop at the end of the title, in Polish or English.
- **Recommended title openings:** "Project…", "Application of…", "Optimisation…", "Comparison…".
- **The APD description has three parts:**
  1. Objective of the thesis, referring to the engineering problem.
  2. Research concept: subject and object of the research, research methods and tools.
  3. Shortened table of contents:
     - Introduction (justification, objective, scope)
     - Literature review
     - Research process methodology
     - Analysis of the current state
     - Project or proposal for improvement
- **Approval:** the topic is fixed before registration for the last semester and submitted in USOS APD by the end of the first month of that semester. The topic card is an APD form; it is not bound into the thesis.

## 2. Structure (6.2), in this order

1. Title page (official FEM template)
2. Table of contents
3. Abstract in Polish
4. Abstract in a foreign language
5. List of symbols, abbreviations and glossary (only if justified)
6. Body of the thesis (Section 3)
7. Bibliography, then the dated list of internet sources
8. List of tables
9. List of figures
10. List of appendices (if any)
11. Appendices, in that order, with page numbers

The seminar slide put the table of contents after the abstracts; edition 12 puts it before them.

## 3. Content (6.3)

The body has three main parts: introduction, substantive presentation of the problem and its solution, and conclusion.

- **Introduction:** justification of the topic, objectives, theoretical and/or empirical problems, scope, general concept, implementation methodology and assumptions. A team thesis also states the division of work.
- **Substantive part:**
  - Literature analysis with references to books, monographs, journals, standards and legal acts. Web sources are allowed only when their author is identified (association, organisation, company).
  - The research or design methods with the **justification of each choice**, the problem analysis, the results, and the concepts and projects developed.
- **Innovativeness and implementation potential:** **mandatory and clearly separated.** Describe the level of novelty against technology and business practice, and the implementation or commercialisation potential. If there is no innovative solution, say so and justify it.
- **Conclusion:** a clear statement of the level to which each objective was achieved, and the conclusions of the research and design work. It must refer to the whole thesis, theoretical and research parts.
- **Length:** at least three publisher's sheets, about **120,000 characters including spaces** (roughly 70–80 pages).
- **Copyright:** the thesis is subject to copyright. The University has priority to publish it; if it does not publish within 6 months of the defence, the student may.

Seminar breakdown of the body, consistent with the above:
1. Introduction
2. Literature review
3. Problem definition and research methodology
4. Research and discussion of results
5. Description of the solution
6. Conclusions

## 4. Formatting (6.4.1)

| Item | Rule |
| --- | --- |
| Font | Times New Roman or Arial, the same throughout |
| Size | Chapter titles 14 pt; subsection titles and text 12 pt |
| Headings | Chapter and subsection titles **bold** |
| Margins | Inner 3.5 cm, outer 2.5 cm, top and bottom 2.5 cm |
| Line spacing | 1.5, no additional space between paragraphs |
| Page numbers | Automatic, on the outer edge; none on the first page (the title page) |
| Alignment | Fully justified |
| Hyphenation | Automatic |
| Paragraphs | Indentation used consistently throughout |
| Chapters | Each main chapter starts on a new page |

## 5. Numbering, language and style (6.4.2)

- **Voice:** impersonal ("research was conducted") or third person ("the author of the thesis stated"). Never "I" or "we".
- **Numbering:** Arabic, 1, 1.1, 1.2, 1.2.1. **No single subpoint:** a 1.2.1 needs a 1.2.2.
- **Emphasis:** **bold only**.
- **Quotations:** italics and quotation marks (Section 7).
- **Headings:** no full stop after a heading; no quotation marks around it.
- **No text between a heading and its first subheading.**
- **Figures, tables and formulas:** a subsection must not start with one, and must not consist only of them. Each one is introduced in the text first.
- **Lists:** consistent bullets or numbers. Items starting with a capital letter end with a full stop (or ! ?); items starting with a lowercase letter end with a comma or semicolon.

## 6. Figures, tables and formulas (6.4.3, 6.4.4)

- **Figures:** caption **below** the figure: "Figure 6.1. Isosceles triangle" (no full stop at the end), then the next line "Source: Nowak, 2007, p. 123; Kowalski, 2009, p. 22". The figure and both lines are centred. Captions of figures taken from foreign-language literature are translated into the thesis language.
- **Tables:** title **above** the table, centred: "Table 6.1. Analysis of employment size". "Source: own elaboration" **below** the table, **left-aligned**. Use one table style throughout.
- **Caption size:** 10 or 11 pt, the same everywhere.
- **Numbering:** chapter.number (Figure 6.1 is the first figure of chapter 6), the same for tables and formulas.
- **Formulas:** on a separate line, centred, number on the right in parentheses: (6.1).
- **Sources:**
  - **Every figure, table and formula has a source.**
  - A redrawn or copied item cites the original; "own elaboration" is not allowed for it.
  - Own photographs are marked "own photograph".
  - Scanned figures are not used.

## 7. References (6.5) and footnotes (6.6)

**In-text citations (Harvard):** surname, year and page in round brackets: (Kowalski, 2001, p. 22).
- Two authors: (Antczak and Bartkowiak, 1994, p. 13).
- Three authors: (Malinowski, Janiak and Nowak, 1999, p. 145).
- More than three authors: (Marczak et al., 2005, p. 12).
- Same surname and same year: add initials, e.g. (Nowak A., 2004, p. 33; Nowak W., 2003, p. 44).
- Several sources in one bracket go in **chronological** order: (Nowak, 1973, p. 22; Malinowski, 1980, p. 55; Adamski, 1999, p. 47).
- No author: give the organisation, e.g. (GUS, 2009), (PKN, 2009), (Journal of Laws No. 44, item 123 of 24.02.2011).
- Direct quotation: quotation marks and italics, with the source.
- A numbered form [15, p. 123] is allowed only by agreement with the supervisor. The GridMind manuscript uses author–date.

**Bibliography:**
- Alphabetical; only sources used in the thesis. Titles without quotation marks.
  - [22] Kowalski A., Nowak J., Management by Objectives, PWN, Warszawa, 2011.
  - [23] Król A., Internal Audit in an Organization, Problemy Jakości nr 11/2009, s. 13-21.
  - [24] Król J., Process Organizations [in:] Modern Management of Organizations, Nowak J. (red.), Wydawnictwo Politechniki Łódzkiej, Łódź, 2011, s. 123-145.
- **Internet sources** follow the bibliography as a separate list with the date of access: www.audytor.pl, 17.06.2019.

**Footnotes:** only for comments, interpretation and comparison, not for references.

## 8. Submission and defence (7, 8)

- **Submission:**
  - The thesis is uploaded to USOS APD and goes automatically to the Uniform Anti-Plagiarism System (JSA); the student declares independent work.
  - The supervisor accepts or rejects the thesis based on the JSA report. The files can be uploaded at most twice.
  - Extension: at most 2 months, by application endorsed by the supervisor.
- **Documents for the dean's office,** at least 5 working days before the exam:
  - clearance slip
  - diploma application
  - achievements for the diploma supplement
  - **division of work** for a team thesis: who wrote which part
- **Exam:**
  - Held within 3 months of the submission deadline.
  - The committee has at least three members (chair, supervisor, reviewer), including a professor or habilitated doctor. Usually on site.
  - Oral, in two parts. First, the thesis presentation, the review and a discussion. Second, **three questions** from the topic list published on fem.put.poznan.pl before the diploma semester.
  - Exam grade = mean of the defence grade and the three answer grades. It is passed if the defence is positive and most answers are positive.
- **Final result** = 0.6 × weighted course average + 0.2 × thesis grade + 0.2 × exam grade:
  - 4.76–5.00 very good with distinction
  - 4.51–4.75 very good
  - 4.21–4.50 good plus
  - 3.81–4.20 good
  - 3.41–3.80 satisfactory plus
  - up to 3.40 satisfactory

## 9. Seminar presentation structure (seminar)

1. Thesis title and supervisor
2. Table of contents
3. Aim of the thesis and the engineering problem
4. Theoretical background with references
5. Concept of solving the problem
6. References

Every table and figure on the slides also needs a source line.

## 10. LaTeX / Overleaf template (`latex/`)

`latex/` is an unofficial, memoir-based project that implements Sections 2 and 4–7. It is adapted from the copyleft PUT CREEF class (Weiss, Wesołek, Szachniuk, Brock). It contains no thesis text and no logos.

| File | Content |
| --- | --- |
| `fem_thesis.cls` | All formatting rules |
| `main.tex` | Front matter, chapters, bibliography and lists in the edition 12 order |
| `chapters/01-introduction.tex` … `06-conclusion.tex` | Skeleton following Section 3 and the APD outline. Chapter 5 holds the mandatory innovativeness section |
| `chapters/examples.tex` | One example of every rule; delete before submission |
| `references.bib` | Demo entries from the regulation examples; replace them |

**Build the Overleaf zip** (from the repository root):
```bash
python -c "import shutil,pathlib; shutil.make_archive(str(pathlib.Path.home()/'Downloads'/'FEM_Thesis_Template'),'zip','.claude/skills/fem-thesis-rules/latex')"
```
Do not use Windows PowerShell 5.1 `Compress-Archive`: it stores `chapters\file.tex` with backslashes, which Overleaf (Linux) does not read as a folder.
In Overleaf: New Project → Upload Project → the zip. The compiler is pdfLaTeX, and Overleaf runs Biber itself. For an engine without Biber, use `\documentclass[english,localcheck]{fem_thesis}` (BibTeX backend). Use `polish` instead of `english` for a thesis written in Polish.

**Where each rule is implemented:**

| Rule | Implementation |
| --- | --- |
| Times, 12 pt, A4 | `newtxtext`/`newtxmath` (pdfLaTeX) or TeX Gyre Termes (XeLaTeX/LuaLaTeX); `12pt,a4paper` |
| Margins 3.5/2.5/2.5/2.5 cm | `\setlrmarginsandblock{3.5cm}{2.5cm}`, `\setulmarginsandblock{2.5cm}{2.5cm}` |
| 1.5 spacing, no paragraph gap | `\baselinestretch` 1.428 (20.7 pt baseline, as in a word processor; floats single-spaced), `\parskip` 0 |
| Consistent indentation | `indentfirst`, `\parindent` 1.25 cm |
| Page numbers on the outer edge, none on the title page | page style `fem` (footer), `\femtitlepage` uses `empty` |
| Chapter titles 14 pt bold, new page; sections 12 pt bold | chapter style `fem`, `\setsecheadstyle` |
| Numbering 1., 1.1., 1.2.1. | `\setsecnumformat`, `\cftXaftersnum` |
| Figure caption below, table caption above, 11 pt, "Figure 2.1." | memoir caption settings; place `\caption` after the figure, before the tabular |
| Source lines | `\figsource{…}` centred, `\tabsource{…}` left-aligned, `\eqsource{…}` under a formula |
| Bold-only emphasis; quotations | `\femem{…}`; `\femquote{…}` gives italics and quotation marks |
| Harvard citations | `\parencite[22]{key}` gives (Kowalski, 2001, p. 22); `\parencites[22]{a}[55]{b}` for several sources, typed in chronological order (not sorted automatically); `\cite` without brackets inside source lines |
| Bibliography style, internet list | `bibstyle=numeric` with custom macros; `@online` entries (url, urldate) print in the separate list; `\femreferences` prints both |
| Abstracts, abbreviations, lists | `femabstractpl` / `femabstract` environments; `\listoftables`, `\listoffigures`, `\listofappendices`; `\femappendices` + `\femappendix{…}` |

**Known limits; check these on Overleaf before writing:**
- The title page is a **placeholder.** Replace it with the official FEM title page.
- Same-surname, same-year disambiguation by initials is not automatic (`uniquename=false`). Add the initial by hand when it happens.
- "s." / "nr" in the regulation example are the Polish forms. The English template prints "p." / "no.".
- **First compile on Overleaf:**
  - measure the margins and the line spacing
  - check that the page numbers sit on the outer edge, with none on page 1
  - check the order: contents before the abstracts, lists after the bibliography
  - check the caption positions, the source alignment and the reference strings against Sections 6–7

## 11. Applying this to GridMind

- Keep the evidence labels of `docs/SCIENTIFIC_RELEASE.md` (measured, assumed, computed, proposed). Do not present Irish community savings as Polish trading profit.
- The title, *przedmiot*, *podmiot* and objective wording must match the title approved in USOS APD; the team confirms it (`docs/SUBMISSION_STATUS.md`). Propose wording; never assert the approved title.
- The objective must be measurable: name the endpoint and the data period actually used.
- The methodology chapter justifies each choice against the alternatives:
  - IPPO/MAPPO and PPO
  - MILP/MPC
  - Ridge and LEAR forecasts
  - block bootstrap
  - signed ledger versus smart contract
- The innovativeness and implementation section is mandatory. It is the place for implementation potential, e.g. the daily battery plan for households, communities and traders, and for its limits.
- The conclusion states the achievement of each objective, including the ones only partly met (the Polish test, if not yet run).
- Exploratory October work (`docs/OCTOBER_ADDENDUM_DRAFT.md`) enters the thesis only as the team and supervisor decide.
- **Thesis text stays out of the public repository** until submission, so the anti-plagiarism check cannot match it against an indexed copy. The template lives here; the thesis is written on Overleaf.

## 12. Review checklist (edition 12)

Report each item as met, not met or not verifiable from the files at hand:

- [ ] Title: engineering form, no full stop, matches the APD card; *przedmiot*, *podmiot* and objective stated
- [ ] Objective is measurable (endpoint, data, period)
- [ ] Order: title page → contents → Polish abstract → foreign abstract → abbreviations (if any) → body → bibliography → internet sources → list of tables → list of figures → list of appendices → appendices
- [ ] Introduction: justification, objectives, problems, scope, concept, methodology, assumptions; division of work for a team
- [ ] Methodology justifies every method, technique and tool
- [ ] Clearly separated innovativeness and implementation/commercialisation section (or a justified absence)
- [ ] Conclusion: level of each objective achieved; covers the whole thesis
- [ ] About 120,000 characters with spaces or more
- [ ] Literature: books, monographs, journals, standards, legal acts; web sources with an identified author
- [ ] Formatting: Times or Arial; 14/12 pt; bold headings; margins 3.5/2.5/2.5/2.5 cm; 1.5 spacing without paragraph gaps; page numbers on the outer edge and none on page 1; fully justified; hyphenation; consistent indentation; chapters on a new page
- [ ] Style: impersonal voice; Arabic numbering with no single subpoint; bold-only emphasis; no full stops after headings; no text between a heading and its subheading; no subsection starting with or consisting only of a figure, table or formula; list punctuation
- [ ] Figures: caption below, centred, chapter numbering, source line; tables: title above, centred, source below and left-aligned; formulas centred, (n.m) on the right, source given; captions 10 or 11 pt consistently
- [ ] Harvard citations with page numbers; et al. after three authors; chronological order inside one bracket; quotations in italics and quotation marks
- [ ] Bibliography alphabetical in the regulation format, titles without quotation marks; separate dated internet sources; only sources actually used
- [ ] Footnotes only for comments
- [ ] Seminar slides follow the six-part structure
