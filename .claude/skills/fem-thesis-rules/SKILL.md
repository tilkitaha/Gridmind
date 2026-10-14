---
name: fem-thesis-rules
description: Poznan University of Technology, Faculty of Engineering Management (FEM) rules for the engineering/diploma thesis, taken from the diploma seminar (Seminarium) slides and notes. Use when writing, restructuring, formatting or reviewing the GridMind thesis, its abstracts, title, APD/USOS description, bibliography, tables and figures, or the seminar/defense presentation. Also use for Turkish requests such as "tez yapısı", "tez formatı", "başlık nasıl olmalı", "kaynakça", "tablo kaynağı", "seminer sunumu", "giriş/sonuç bölümü", "sayfa sayısı".
---

# FEM diploma thesis rules (Seminarium)

Source: diploma seminar slides photographed on 14 October 2026, plus handwritten notes from the same session. The faculty template at www.fem.put.poznan.pl (student area / documents / templates of diploma documents) and the faculty regulations (issue 12, in force from 1 October 2025; see `docs/SUBMISSION_STATUS.md`) take precedence where they differ. When a rule below conflicts with the template, follow the template and say so.

## 1. Topic and title (thesis description in USOS APD)

- The topic must relate to an **engineering concept, project or process**, address an **engineering problem and propose a solution**.
- The thesis must state clearly:
  - **Object of research**: what is analysed or designed.
  - **Subject of research**: where, i.e. in which organisation, facility or system the analysis is conducted.
  - **Objective/goal**: what is to be achieved, e.g. optimisation, enhancement or improvement.
- Recommended title forms: "Design of …", "Application of …", "Optimization of …", "Comparison of …".

Example from the seminar notes, showing the pattern rather than our topic:

> *Evaluation of Publicly Available AI Models in Detecting Misleading Advertising Content in Digital Marketing*
> Object: publicly available AI models used to detect misleading advertising content.
> Subject: digital marketing, i.e. online advertisements on websites and social media.
> Objective: compare selected AI models and identify the most accurate one.
> The goal is then broken into steps: identify and analyse the problem → test the selected models on a data set → compare results and select the best.

## 2. Engineering thesis features

- **Thesis entity**: a single company, workplace or system that allows a dedicated solution to be developed.
- **Thesis goal**: a practical objective requiring an engineering approach, formulated with **SMART** logic (specific, measurable, achievable, relevant, time-bound).
- **Research methodology**: methods, techniques and tools suitable for an engineering or managerial problem. The methodology must be described, and **justifying the choice of methods, techniques and tools is mandatory**.
- **Literature sources**: specialist literature, several items, covering books, periodicals, papers and standards.
- **Volume**: at least three publishing sheets, i.e. **120,000 typographic characters including spaces**, which is roughly **70–80 pages**.

## 3. Required arrangement, in this order

1. Title page, using the faculty template.
2. Abstract in Polish.
3. Abstract in a foreign language.
4. Table of contents.
5. List of symbols, abbreviations and glossary, only if justified.
6. Thesis content (Section 4).
7. Bibliography (literature list).
8. List of tables and list of figures.
9. List of attachments, if any, followed by the attachments in that order.

The diploma thesis card is **no longer** included; it was struck out on the slide.

## 4. Content chapters

1. **Introduction**: goal and scope of the work, and the structure of the thesis.
2. **Literature review**: key concepts based on the literature.
3. **Definition of the problem and research methodology**: the problem and scope, with a detailed description of the selected methods, techniques and tools and their **justification**.
4. **Research and discussion of results.**
5. **Description of the solution and conclusions.**
6. **Bibliography.**
7. **List of appendices.**

### Introduction must contain

- Justification of the subject choice.
- Objectives.
- Theoretical and/or empirical problems to be solved.
- Scope of the work.
- General concept and methodology of developing the thesis, and its **assumptions**.

### Summary (closing chapter) must contain

- **Intellectual property and implementation possibility analysis.**
- A clear statement of the **level to which each objective was achieved**, and the conclusions of the research and conceptual-design work.
- Reference to the **entire content**, both theoretical and research parts.
- Note: the thesis is subject to copyright, and the University has priority in publishing it.

## 5. Technical formatting

| Item | Rule |
| --- | --- |
| Font | Times New Roman or Arial, the same throughout |
| Size | Section titles 14 pt; subsection titles and body text 12 pt |
| Margins | Inner 3.5 cm, outer 2.5 cm, top and bottom 2.5 cm |
| Line spacing | 1.5, without extra spacing between paragraphs |
| Page numbers | Automatic, bottom right; none on the first (title) page |
| Alignment | The slide says "centre-justified"; read this as fully justified body text and check the template |
| Hyphenation | Automatic |
| Indentation | Either always or never, consistently |
| Template | Start from the faculty thesis file template, already formatted to these rules |

## 6. Citations, tables and figures

- **Harvard style** (author-date) in the text. The faculty allows a numbered style by agreement; the GridMind manuscript currently uses author-date.
- Bibliography in **alphabetical order**.
- Label above the table or figure, e.g. "Tab. 1" followed by the title. The source line goes **below**:
  - copied unchanged: `Source: Katkowska J., 2026, p. 38`
  - adapted from a source: `Source: own study based on Katkowska J., 2026, p. 38`
  - entirely the authors' own: `Source: own study`
- Every table and figure needs a source line, including the authors' own results.

## 7. Seminar presentation structure

1. Thesis title and tutor (supervisor) name.
2. Table of contents.
3. Aim of the thesis and the characteristics of the engineering problem to be solved.
4. Theoretical background of problem solving: a literature study including references.
5. Concept of solving the engineering problem.
6. List of references (bibliography).

## 8. Applying this to GridMind

- Keep the evidence labels of `docs/SCIENTIFIC_RELEASE.md` (measured, assumed, computed, proposed) when writing the object, subject and goal. Do not present Irish community savings as Polish trading profit.
- The object, subject and objective wording must match the title approved in USOS APD; the team confirms it (`docs/SUBMISSION_STATUS.md`). Propose wording, never assert the approved title.
- A SMART goal must name a measurable endpoint and data period, e.g. the paired cost metric and dates actually used.
- The methodology chapter must justify each method choice (IPPO/MAPPO, MPC, Ridge, block bootstrap, signed ledger) against alternatives, not only describe it.
- The Summary needs an explicit intellectual-property and implementation-possibility section, and a per-objective statement of achievement, including objectives only partly met (Polish study, untouched test).
- Exploratory October work (`docs/OCTOBER_ADDENDUM_DRAFT.md`) enters the thesis only as the team and supervisor decide.

## 9. Review checklist

Report each item as met, not met or not verifiable from the files at hand:

- [ ] Title uses an engineering form and matches the APD description
- [ ] Object, subject and objective are stated explicitly
- [ ] Goal is SMART
- [ ] Order: title page → PL abstract → foreign abstract → contents → abbreviations (if any) → content → bibliography → tables/figures lists → attachments
- [ ] Introduction: subject justification, objectives, problems, scope, concept, methodology, assumptions
- [ ] Methodology chapter justifies every method, technique and tool
- [ ] Summary: IP and implementation possibility analysis, per-objective achievement, covers the whole work
- [ ] At least 120,000 characters with spaces (about 70–80 pages)
- [ ] Literature includes books, periodicals, papers and standards
- [ ] Formatting: font, 14/12 pt, margins 3.5/2.5/2.5/2.5 cm, 1.5 spacing, no paragraph spacing, page numbers bottom right and none on page 1, justified, hyphenation, consistent indentation
- [ ] Harvard citations; bibliography alphabetical
- [ ] Every table and figure has a label above and a source line below in one of the three forms
- [ ] Seminar slides follow the six-part presentation structure
