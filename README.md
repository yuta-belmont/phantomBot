# phantomBot
Recover your phantom wallet if you are missing a word.
Go to my YouTube for the explanation and setup walkthru.
https://www.youtube.com/channel/UC8fMpp4JE90b92PNtoByK2A

If your have your recovery phrase, but it's missing a word... The missing word could go in any location and be any one of the 2048 possible words (see english.txt file).
This script uses the checksum to narrow the search space by ~16x. Technically in each position the script only has to try about 132 words (the missing word can be in any position 1-12).
So total permutations should be around 132*12 = ~1500 attempts.
