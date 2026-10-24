%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% fem_thesis.cls -- engineering thesis, Faculty of Engineering           %%
%% Management, Poznan University of Technology                           %%
%%                                                                       %%
%% Follows the FEM "Regulations on the Completion of Diploma Theses",    %%
%% edition 12, in force from 02.10.2025 (the Polish version is binding). %%
%% UNOFFICIAL: not endorsed by the Faculty or the University.            %%
%%                                                                       %%
%% Adapted from put_creef_thesis.cls (copyleft): (c) 2006-2011 Dawid     %%
%% Weiss, 2012-2017 Przemyslaw Wesolek, 2020- Marta Szachniuk,           %%
%% 2023-2025 S. Brock, Poznan University of Technology.                  %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}[2020/10/01]
\ProvidesClass{fem_thesis}[2026/10/24 v1.0 FEM PUT thesis, regulations ed. 12]

% Options: english (default) or polish main language; localcheck builds the
% bibliography with BibTeX instead of Biber (for engines without Biber).
\newif\if@fempolish \@fempolishfalse
\newif\if@femlocal  \@femlocalfalse
\DeclareOption{english}{\@fempolishfalse}
\DeclareOption{polish}{\@fempolishtrue}
\DeclareOption{localcheck}{\@femlocaltrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{memoir}}
\ProcessOptions\relax

% 6.4.1: body text 12 pt, A4, one-sided.
\LoadClass[12pt,a4paper,oneside,openany]{memoir}

%--------------------------------------------------------------------------
% Fonts and language
%--------------------------------------------------------------------------
\RequirePackage{amsmath}                 % before newtxmath / unicode-math
\RequirePackage{iftex}
\ifPDFTeX
  \RequirePackage[T1]{fontenc}
  \RequirePackage{newtxtext,newtxmath}   % 6.4.1: Times New Roman (Times)
\else
  \RequirePackage{unicode-math}
  \setmainfont{TeX Gyre Termes}          % Times metrics
  \setmathfont{TeX Gyre Termes Math}
\fi
\if@fempolish
  \RequirePackage[english,main=polish]{babel}
\else
  \RequirePackage[polish,main=english]{babel}
\fi
\RequirePackage{indentfirst}             % 6.4.1: indent every paragraph
\RequirePackage[autostyle]{csquotes}
\IfFileExists{microtype.sty}{\RequirePackage{microtype}}{}
\RequirePackage{graphicx}
\RequirePackage{booktabs}

%--------------------------------------------------------------------------
% Page layout (6.4.1)
%--------------------------------------------------------------------------
\setstocksize{297mm}{210mm}
\settrimmedsize{297mm}{210mm}{*}
\settrims{0pt}{0pt}
\setlrmarginsandblock{3.5cm}{2.5cm}{*}   % inner 3.5 cm, outer 2.5 cm
\setulmarginsandblock{2.5cm}{2.5cm}{*}   % top and bottom 2.5 cm
\setheadfoot{\onelineskip}{1.2cm}        % page number sits in the bottom margin
\setheaderspaces{*}{\onelineskip}{*}
\checkandfixthelayout

% Line spacing 1.5 as in a word processor: 1.5 x 13.8 pt = 20.7 pt for
% 12 pt Times; memoir's 12 pt baselineskip is 14.5 pt, so the factor is 1.428.
% Tables and figures keep single spacing inside the float.
\renewcommand{\baselinestretch}{1.428}
\AddToHook{env/table/begin}{\SingleSpacing}
\AddToHook{env/figure/begin}{\SingleSpacing}
\setlength{\parskip}{0pt}                % no extra space between paragraphs
\setlength{\parindent}{1.25cm}

% Automatic page numbers on the outer edge (right on one-sided pages),
% no running heads, no number on the title page.
\makepagestyle{fem}
\makeevenhead{fem}{}{}{}
\makeoddhead{fem}{}{}{}
\makeevenfoot{fem}{\thepage}{}{}
\makeoddfoot{fem}{}{}{\thepage}
\pagestyle{fem}
\aliaspagestyle{chapter}{fem}
\aliaspagestyle{plain}{fem}

%--------------------------------------------------------------------------
% Headings (6.4.1, 6.4.2)
%--------------------------------------------------------------------------
% Chapter titles 14 pt bold, numbered "1.", each chapter on a new page;
% section titles 12 pt bold; no full stop after the title text.
\newcommand{\femchapterfont}{\normalfont\fontsize{14}{17}\selectfont\bfseries}
\makechapterstyle{fem}{%
  \renewcommand{\chapterheadstart}{}%
  \renewcommand{\printchaptername}{}%
  \renewcommand{\chapternamenum}{}%
  \renewcommand{\chapnumfont}{\femchapterfont}%
  \renewcommand{\chaptitlefont}{\femchapterfont\raggedright}%
  \renewcommand{\printchapternum}{\chapnumfont\thechapter.\space}%
  \renewcommand{\afterchapternum}{}%
  \renewcommand{\printchapternonum}{}%
  \renewcommand{\printchaptertitle}[1]{\chaptitlefont ##1}%
  \renewcommand{\afterchaptertitle}{\par\nobreak\vskip\onelineskip}%
}
\chapterstyle{fem}
\setsecheadstyle{\normalfont\normalsize\bfseries\raggedright}
\setsubsecheadstyle{\normalfont\normalsize\bfseries\raggedright}
\setsubsubsecheadstyle{\normalfont\normalsize\bfseries\raggedright}
\setsecnumformat{\csname the#1\endcsname.\quad}
\setsecnumdepth{subsubsection}           % 1, 1.1, 1.2.1 in Arabic numerals
\maxsecnumdepth{subsubsection}
\settocdepth{subsubsection}
\renewcommand{\cftchapteraftersnum}{.}
\renewcommand{\cftsectionaftersnum}{.}
\renewcommand{\cftsubsectionaftersnum}{.}
\renewcommand{\cftsubsubsectionaftersnum}{.}

%--------------------------------------------------------------------------
% Captions and sources (6.4.3, 6.4.4)
%--------------------------------------------------------------------------
% Caption size 11 pt everywhere (10 or 11 pt is allowed if consistent).
% "Figure 2.1. Title" centred BELOW the figure, then \figsource.
% "Table 2.1. Title" centred ABOVE the table, \tabsource below, left-aligned.
\newcommand{\femcaptionsize}{\fontsize{11}{13.6}\selectfont}
\captionnamefont{\femcaptionsize}
\captiontitlefont{\femcaptionsize}
\captiondelim{.\space}
\captionstyle{\centering}
\setlength{\belowcaptionskip}{4pt}
\newcommand{\femsourcename}{Source}
\newcommand{\figsource}[1]{\par{\centering\femcaptionsize\femsourcename: #1\par}}
\newcommand{\tabsource}[1]{\par\vspace{4pt}{\raggedright\femcaptionsize\femsourcename: #1\par}}
\newcommand{\eqsource}[1]{\par{\centering\femcaptionsize\femsourcename: #1\par}\vspace{\onelineskip}}

% 6.4.2: emphasis only in bold; quotations in italics and quotation marks.
\newcommand{\femem}[1]{\textbf{#1}}
\newcommand{\femquote}[1]{\enquote{\textit{#1}}}

%--------------------------------------------------------------------------
% Front matter, lists and appendices (6.2)
%--------------------------------------------------------------------------
\newcommand{\femfield}[1]{\def\@femfield{#1}}
\newcommand{\femsupervisor}[1]{\def\@femsupervisor{#1}}
\newcommand{\femyear}[1]{\def\@femyear{#1}}
\newcommand{\femthesistype}[1]{\def\@femthesistype{#1}}
\femfield{Engineering Management}
\femsupervisor{}
\femyear{\the\year}
\newcommand{\album}[1]{\unskip,~album no.~#1}

% PLACEHOLDER title page. Replace its layout with the official FEM title
% page template (fem.put.poznan.pl > Student > templates of diploma
% documents); it is counted as page 1 and carries no page number.
\newcommand{\femtitlepage}{%
  \begingroup
  \thispagestyle{empty}%
  \SingleSpacing
  \begin{center}
    {\large POZNAN UNIVERSITY OF TECHNOLOGY\\[2pt]
     FACULTY OF ENGINEERING MANAGEMENT\par}
    \vspace{6pt}
    {Field of study: \@femfield\par}
    \vspace{3.5cm}
    {\large\@femthesistype\par}
    \vspace{1cm}
    {\fontsize{16}{20}\selectfont\bfseries\@title\par}
    \vspace{1.5cm}
    {\renewcommand{\and}{\\}\large\@author\par}
    \vfill
    {Supervisor\\\@femsupervisor\par}
    \vspace{2cm}
    {POZNAŃ \@femyear\par}
  \end{center}
  \endgroup
  \clearpage}

% Abstracts: \begin{femabstract}{Heading}{keywords line} ... \end{femabstract}
\newenvironment{femabstract}[2]{%
  \chapter*{#1}\addcontentsline{toc}{chapter}{#1}%
  \def\@femkeywords{#2}}{%
  \par\vspace{\onelineskip}\noindent\@femkeywords\par}
\newenvironment{femabstractpl}[2]{%
  \begin{otherlanguage}{polish}\begin{femabstract}{#1}{#2}}{%
  \end{femabstract}\end{otherlanguage}}

% List of appendices; \femappendices starts the appendices, and each
% \femappendix{Title} is numbered A, B, ... and entered in that list.
\newcommand{\femloaname}{List of appendices}
\newlistof{listofappendices}{loa}{\femloaname}
\newcommand{\femappendices}{%
  \appendix
  \renewcommand{\printchapternum}{\chapnumfont\appendixname~\thechapter.\space}}
\newcommand{\femappendix}[1]{%
  \chapter{#1}%
  \addcontentsline{loa}{chapter}{\protect\numberline{\thechapter}#1}}

%--------------------------------------------------------------------------
% Literature references: Harvard system (6.5)
%--------------------------------------------------------------------------
% In text: (Kowalski, 2001, p. 22) with \parencite[22]{key}; two authors
% joined by "and"; three authors "A, B and C"; more than three "et al.".
% Bibliography: alphabetical, numbered [n], "Kowalski A., Nowak J., Title,
% Publisher, City, Year."; internet sources listed separately with the
% date of access.
\if@femlocal
  \PassOptionsToPackage{backend=bibtex}{biblatex}
\else
  \PassOptionsToPackage{backend=biber}{biblatex}
\fi
\RequirePackage[
  bibstyle=numeric, citestyle=authoryear,
  sorting=nyt, sortcites=false, defernumbers=true,
  maxcitenames=3, mincitenames=1, maxbibnames=99,
  giveninits=true, uniquename=false, uniquelist=false,
  dashed=false, isbn=false, doi=false, eprint=false,
  urldate=short, datezeros=true]{biblatex}

\DeclareNameAlias{default}{family-given}
\DeclareNameAlias{sortname}{family-given}
\def\revsdnamepunct{}                         % "Kowalski A." (no comma)
\DeclareDelimFormat{nameyeardelim}{\addcomma\space}
\DeclareDelimFormat{finalnamedelim}{\addspace\bibstring{and}\space}
\DeclareDelimFormat[bib,biblist]{finalnamedelim}{\addcomma\space}
\renewcommand*{\newunitpunct}{\addcomma\space}
\renewcommand*{\newblockpunct}{\addcomma\space}

% Titles without quotation marks or italics.
\DeclareFieldFormat*{title}{#1}
\DeclareFieldFormat{journaltitle}{#1}
\DeclareFieldFormat{booktitle}{#1}
\DeclareFieldFormat{url}{\url{#1}}
\DeclareFieldFormat{urldate}{#1}

% Publisher, City, Year.
\renewbibmacro*{publisher+location+date}{%
  \printlist{publisher}%
  \setunit*{\addcomma\space}%
  \printlist{location}%
  \setunit*{\addcomma\space}%
  \usebibmacro{date}%
  \newunit}
% Journal no. 11/2009
\renewbibmacro*{journal+issuetitle}{%
  \usebibmacro{journal}%
  \setunit*{\addspace}%
  \iffieldundef{number}
    {\setunit*{\addcomma\space}\printdate}
    {\printtext{\bibstring{number}\addnbspace\printfield{number}\addslash\printdate}}%
  \newunit}
% Chapter in an edited book: "Title [in:] Book, Nowak J. (ed.), ..."
\renewbibmacro*{in:}{%
  \ifentrytype{article}{}{\printtext{[\bibstring{in}:]}\setunit{\addspace}}}
\renewbibmacro*{byeditor+others}{%
  \ifnameundef{editor}{}{%
    \printnames[family-given]{editor}%
    \setunit{\addspace}%
    \printtext[parens]{\bibstring{editor}}%
    \clearname{editor}%
    \newunit}%
  \usebibmacro{bytranslator+others}}
% Internet sources: "address, dd.mm.yyyy"
\DeclareBibliographyDriver{online}{%
  \usebibmacro{bibindex}%
  \usebibmacro{begentry}%
  \printfield{url}%
  \setunit{\addcomma\space}%
  \printurldate
  \usebibmacro{finentry}}
\defbibenvironment{femweb}
  {\list{}{\setlength{\leftmargin}{0pt}\setlength{\itemindent}{0pt}%
           \setlength{\itemsep}{0pt}}}
  {\endlist}
  {\item}
\DefineBibliographyStrings{english}{in = {in}, editor = {ed.}, editors = {eds.}}
\DefineBibliographyExtras{english}{%
  \protected\def\mkbibdateshort#1#2#3{%
    \iffieldundef{#3}{}{\mkdayzeros{\thefield{#3}}.}%
    \iffieldundef{#2}{}{\mkmonthzeros{\thefield{#2}}.}%
    \iffieldbibstring{#1}{\bibstring{\thefield{#1}}}{\mkyearzeros{\thefield{#1}}}}}

\newcommand{\fembibname}{Bibliography}
\newcommand{\femwebname}{Internet sources}
% Bibliography, then the separate dated list of internet sources.
\newcommand{\femreferences}{%
  \printbibliography[nottype=online, heading=bibintoc, title={\fembibname}]%
  \printbibliography[type=online, env=femweb, heading=subbibintoc, title={\femwebname}]}

%--------------------------------------------------------------------------
% Polish names, when the thesis is written in Polish
%--------------------------------------------------------------------------
\if@fempolish
  \femthesistype{Praca dyplomowa inżynierska}
  \renewcommand{\femsourcename}{Źródło}
  \renewcommand{\fembibname}{Bibliografia}
  \renewcommand{\femwebname}{Źródła internetowe}
  \renewcommand{\femloaname}{Spis załączników}
  \addto\captionspolish{\renewcommand{\figurename}{Rysunek}%
                        \renewcommand{\tablename}{Tabela}%
                        \renewcommand{\appendixname}{Załącznik}}
\else
  \femthesistype{Engineering thesis}
\fi

%--------------------------------------------------------------------------
% Links (black, so the printed thesis looks the same)
%--------------------------------------------------------------------------
\RequirePackage{url}
\RequirePackage[unicode,bookmarks,bookmarksnumbered]{hyperref}
\hypersetup{colorlinks=true, linkcolor=black, citecolor=black,
  urlcolor=black, filecolor=black, pdfpagemode=UseOutlines}

\pagenumbering{arabic}
