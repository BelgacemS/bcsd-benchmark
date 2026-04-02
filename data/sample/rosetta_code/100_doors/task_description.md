# 100 doors

There are 100 doors in a row that are all initially closed. 

You make 100 passes by the doors. 

The first time through, visit every door and toggle the door (if the door is closed, open it; if it is open, close it). 

The second time, only visit every 2nd door (door #2, #4, #6, ...), and toggle it.  

The third time, visit every 3rd door (door #3, #6, #9, ...), etc, until you only visit the 100th door.

;Task:
Answer the question: what state are the doors in after the last pass? Which are open, which are closed?

Alternate:  
As noted in this page's discussion page, the only doors that remain open are those whose numbers are perfect squares.

Opening only those doors is an optimization that may also be expressed; 
however, as should be obvious, this defeats the intent of comparing implementations across programming languages.

;Why doesn't syntax highlighting work on this page ?:
Currently, there is a limit on how many &lt;syntaxhighlight&gt; tags can appear on a page, so only the first few languages get highlighting, the rest are shown in monochrome.
You could try "manual highlighting", possibly using one of the highlighters on Syntax highlighting using Mediawiki formatting or something similar.
