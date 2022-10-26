# Smartling/Pontoon glossary compare documentation

## Summary

This tool takes a glossary export from Smartling and a Pontoon locale export as input, and exports a csv list of terms that only exist in the Smartling export.

## Syntax

Call glossary_compare.py from your command line, with the following arguments:

--smartling *filepath*  
(***Required***) Designate the filepath of a .tbx (version 2) file that contains the list of terminology exported from Smartling.

--pontoon *filepath*  
(***Required***) Designate the filepath of a .tbx (version 2) file that contains the list of terminology exported from Pontoon.

## Output

This script outputs a csv file in the directory this script was run.
