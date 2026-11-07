%% comjnl.cls -- LOCAL SHIM (NOT the official Oxford University Press class)
%%
%% The official `comjnl.cls` for The Computer Journal is distributed by OUP with
%% the journal's author kit and is not available on this machine (OUP and CTAN
%% mirrors returned HTTP 403/404).  This file reproduces the *interface* used by
%% the journal's sample file -- \copyrightyear, \vol, \issue, \DOI, \title[short],
%% \author, \affiliation, \email, \shortauthors, \received, \revised, \category,
%% \terms, \keywords, \ack -- and a single-column layout close to the journal's.
%%
%% At submission: delete this file, drop the official comjnl.cls and compj.bst
%% into this directory, and change \bibliographystyle{plainnat} to
%% \bibliographystyle{compj}.  Nothing else in main.tex needs to change.
%%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{comjnl}[2026/11/07 v0.1 local shim for The Computer Journal]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass[11pt,a4paper]{article}

\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{newtxtext,newtxmath}
\RequirePackage[margin=2.35cm,top=2.2cm,bottom=2.4cm]{geometry}
\RequirePackage{amsmath}
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{caption}
\RequirePackage{xcolor}
\RequirePackage[round,authoryear]{natbib}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{microtype}
\RequirePackage{enumitem}

\captionsetup{font=small,labelfont=bf,skip=4pt}
\setlist[itemize]{leftmargin=1.35em,itemsep=1pt,topsep=2pt}
\renewcommand{\arraystretch}{1.04}
\setlength{\parskip}{0pt}
\setlength{\parindent}{1.2em}

% ------------------------------------------------------------------ metadata
\def\@copyrightyear{}\def\@vol{}\def\@issue{}\def\@DOI{}
\def\@shortauthors{}\def\@received{}\def\@revised{}
\def\@keywords{}\def\@terms{}
\newcommand{\copyrightyear}[1]{\def\@copyrightyear{#1}}
\newcommand{\vol}[1]{\def\@vol{#1}}
\newcommand{\issue}[1]{\def\@issue{#1}}
\newcommand{\DOI}[1]{\def\@DOI{#1}}
\newcommand{\shortauthors}[1]{\def\@shortauthors{#1}}
\newcommand{\received}[1]{\def\@received{#1}}
\newcommand{\revised}[1]{\def\@revised{#1}}
\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newcommand{\terms}[1]{\def\@terms{#1}}

\let\@jtitle\@empty
\let\@shorttitle\@empty
\renewcommand{\title}[2][]{%
  \def\@shorttitle{#1}\def\@jtitle{#2}}
\let\@jauthor\@empty
\let\@jaffil\@empty
\let\@jemail\@empty
\let\@jorcid\@empty
\renewcommand{\author}[1]{\def\@jauthor{#1}}
\newcommand{\affiliation}[1]{\def\@jaffil{#1}}
\newcommand{\email}[1]{\def\@jemail{#1}}
\newcommand{\orcid}[1]{\def\@jorcid{#1}}

\newcommand{\category}[3]{\par\noindent\textbf{#1}: #2 --- #3\par}

% ------------------------------------------------------------------ title page
\renewcommand{\maketitle}{%
  \thispagestyle{empty}%
  \begin{center}
    {\LARGE\bfseries \@jtitle\par}
    \vspace{1.1em}
    {\large \@jauthor\par}
    \vspace{0.5em}
    {\small\itshape \@jaffil\par}
    \ifx\@jemail\@empty\else{\small\ttfamily \@jemail\par}\fi
    \ifx\@jorcid\@empty\else{\small ORCID: \@jorcid\par}\fi
  \end{center}
  \vspace{0.6em}
  \ifx\@received\@empty\else
    \begin{center}\footnotesize
      \ifx\@received\@empty\else \@received\fi
      \ifx\@revised\@empty\else ; revised \@revised\fi
    \end{center}
  \fi
  \vspace{0.7em}%
}

% ------------------------------------------------------------------ abstract
\renewenvironment{abstract}{%
  \begin{center}\begin{minipage}{0.93\linewidth}%
  \small\noindent\textbf{Abstract}\par\vspace{0.35em}\small\noindent\ignorespaces
}{%
  \end{minipage}\end{center}\vspace{0.6em}%
}

\newcommand{\@printkeywords}{%
  \ifx\@keywords\@empty\else
    \begin{center}\begin{minipage}{0.93\linewidth}\small
      \noindent\textbf{Keywords:} \@keywords
      \ifx\@terms\@empty\else\par\vspace{0.25em}\noindent\textbf{Terms:} \@terms\fi
    \end{minipage}\end{center}\vspace{0.8em}%
  \fi}

% keywords printed right after \maketitle
\let\@origmaketitle\maketitle
\renewcommand{\maketitle}{\@origmaketitle\@printkeywords}

% ------------------------------------------------------------------ \ack
\newcommand{\ack}[1]{%
  \section*{Acknowledgements}%
  \noindent #1\par\vspace{0.8em}}

\endinput
