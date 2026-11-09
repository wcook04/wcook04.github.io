# One Checkout: commit one fix while another AI keeps editing

short film `short-one-checkout`, 86 s as cut. Machine transcript of Will's recorded take (lower case, recognition errors kept), one sentence per line.

- AI coding assistants edit the same file, saving one assistant's finish fix can also save the other's unfinished edits.
- this is a short summary video of onecheckout which is my tool for trying to solve that problem
- one of a series of short companions to my longer videos
- saving here means making a commit a version of that code recorded by git a program that tracks changes to code
- with onecheckout the assistant with the finish fix supplies a patch a list of the exact lines of that fix and one checkout adds only that patch to the last commit so the assistant can test the fix without the other assistant's unfinished edits
- when the tests pass one checkout commits that version and the file the assistant share still holds both sets of edits
- so nobody has to clear the unfinished work out of the way
- but one checkout does not stop the two assistants overwriting each other's edits in the file
- and it also turns off the checks git normally runs at each commit so assistants have to run the project checks themselves
- this is just a comparison video
- but if you want to look at the longer more detailed video i follow one login fix into a commit show how an older copy of the file can undo that fix and explain when the separate copies of the project make more sense
- you can watch it here
- my agent trace video shows how to reach back what each assistant ran
- and the code on github with a demo you can run and my introduction to the whole project are linked below as well in the description if you'd be interested
- but otherwise thank you very much for watching and hopefully see you in the next video
