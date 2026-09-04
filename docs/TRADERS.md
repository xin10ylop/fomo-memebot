# Trader-by-trader classification (rule-based, from on-chain and fomo data)

Classes: insider_or_allocation = sells tokens never bought on-chain; luck_one_bag = PnL is unrealized appreciation of one early bag; kol_flow_mover = audience large enough to move prices; skill_candidate = repeatable realized profits on fully priced tokens; active_churner_negative = many trades, negative realized; concentrated_bag = one holding dominates; unknown = insufficient priced data.

| # | handle | class | PnL all | PnL/volume | followers | top holding % | liquidity haircut | sampled closed realized | RH realized (fully priced tokens) | sold w/o buy | SOL realized | why |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | unipcs | kol_flow_mover | 12,303,737 | 5.2x | 465,838 | 41% | 60% |  | 66,199 | 68,153 | -24,809 | 465,838 followers |
| 2 | DumbCrayonEater | luck_one_bag | 9,346,034 | 9.2x | 451,299 | 91% | 69% |  | 224,435 | 0 | 147,868 | PnL/volume 9.2x, top holding 91% of portfolio |
| 3 | Salem1299534 | kol_flow_mover | 6,645,513 | 2.8x | 178,623 | 87% | 64% | 975 | -4,815 | 0 | -2,361 | 178,623 followers |
| 4 | Natan_benish | luck_one_bag | 5,238,450 | 415.3x | 77,419 | 95% | 60% | -232 | -65 | 0 | -86 | PnL/volume 415.3x, top holding 95% of portfolio |
| 5 | brrrgrrrz | luck_one_bag | 4,607,643 | 1.2x | 73,104 | 95% | 52% | 159,674 | 889,666 | 37,339 |  | top holding 95%, unrealized 1245244% of PnL |
| 6 | AvgJoesCrypto | concentrated_bag | 3,967,904 | 2.2x | 91,469 | 74% | 37% | -704 | 1,119 | 29,627 | 2,449 | top holding 74% of portfolio |
| 7 | frogmanhaha | concentrated_bag | 3,675,722 | 167.7x | 45,335 | 56% | 45% | -2,935 | 1,107,164 | 0 |  | top holding 56% of portfolio |
| 8 | change | kol_flow_mover | 3,403,010 | 0.1x | 337,473 | 85% | 42% | 378,743 | -14,324 | 123,024 |  | 337,473 followers |
| 9 | notanicecat69 | luck_one_bag | 3,048,131 | 0.5x | 49,469 | 93% | 46% | 49,213 | 434,794 | 508 | 298,546 | top holding 93%, unrealized 87% of PnL |
| 10 | ogle | luck_one_bag | 2,925,016 | 9.4x | 22,779 | 98% | 66% | -32,206 | 93 | 93 | -3,351 | PnL/volume 9.4x, top holding 98% of portfolio |
| 11 | econoar | active_churner_negative | 2,901,083 | 2.1x | 61,037 | 63% | 47% | 5,574 | -737 | 1,828 | -37,642 | sampled realized fomo 5573.943359700001, SOL realized -37642.493352 |
| 12 | ether_monk | kol_flow_mover | 2,774,202 | 0.3x | 318,565 | 24% | 43% | -37,179 | 1,427,039 | 5,625 | -19,458 | 318,565 followers |
| 13 | CardinalSaint2 | concentrated_bag | 2,689,821 | 1.9x | 18,734 | 51% | 27% | 18,331 | 33,802 | 11,556 | 2,196 | top holding 51% of portfolio |
| 14 | 0xAvast | kol_flow_mover | 2,615,986 | 2.1x | 259,736 | 58% | 57% | -69,052 | -348,560 | 373 | -13,462 | 259,736 followers |
| 15 | frankdegods | kol_flow_mover | 2,579,117 | 0.1x | 218,711 | 93% | 65% |  | 21,377 | 3,897 |  | 218,711 followers |
| 16 | LP1111 | luck_one_bag | 2,522,397 | 2.9x | 15,435 | 95% | 41% | 250,228 | -9,825 | 5 | -7,636 | top holding 95%, unrealized 87% of PnL |
| 17 | kyle | unknown | 2,512,253 | 1.8x | 29,180 | 32% | 23% | -14,129 | 18,525 | 579 | -3,352 |  |
| 18 | cosby | luck_one_bag | 2,447,271 | 1.7x | 19,439 | 87% | 41% | -61,976 | 40,610 | 0 | 13 | top holding 87%, unrealized 98% of PnL |
| 19 | inyourwalls | luck_one_bag | 2,396,864 | 0.8x | 32,655 | 75% | 34% | -54,449 | 634,352 | 726 | -79,681 | top holding 75%, unrealized 74% of PnL |
| 20 | Chubbi230 | luck_one_bag | 2,300,461 | 27.4x | 13,124 | 78% | 40% | 6,017 | 684,881 | 1,347 |  | PnL/volume 27.4x, top holding 78% of portfolio |
| 21 | RugDalio | luck_one_bag | 2,102,203 | 6.0x | 13,909 | 96% | 40% | 14,240 | 18,904 | 66 | -243 | PnL/volume 6.0x, top holding 96% of portfolio |
| 22 | soby0x | luck_one_bag | 2,078,728 | 3.1x | 14,848 | 72% | 34% | 78,540 | 29,259 | 45 | -486 | PnL/volume 3.1x, top holding 72% of portfolio |
| 23 | lordarbiter | luck_one_bag | 2,078,088 | 2.0x | 12,566 | 96% | 39% | -4,021 | -597 | 11 | -15,837 | top holding 96%, unrealized 96% of PnL |
| 24 | SolSwizzle | luck_one_bag | 2,076,234 | 0.3x | 35,754 | 92% | 47% | -48,862 | 147,706 | 2,466 | -262,071 | top holding 92%, unrealized 131% of PnL |
| 25 | PoorGoat_ | kol_flow_mover | 2,070,396 | 1.4x | 497,828 | 44% | 61% |  | -2,031 | 575 |  | 497,828 followers |
| 26 | aki11a | luck_one_bag | 2,056,895 | 1.9x | 13,043 | 98% | 39% | 75,194 | 83,889 | 9,376 | -55,614 | top holding 98%, unrealized 92% of PnL |
| 27 | 0xnobi | luck_one_bag | 1,937,724 | 1.8x | 38,076 | 97% | 36% | -18,205 | 832 | 419 | -6,655 | top holding 97%, unrealized 97% of PnL |
| 28 | Quanterty | insider_or_allocation | 1,889,895 | 0.3x | 260,773 | 58% | 42% | -91,007 | 841,361 | 816,331 | 12,363 | sold $816,331 of tokens never bought on-chain |
| 29 | picadura | luck_one_bag | 1,853,205 | 0.4x | 17,377 | 83% | 32% | -1,308 | -6,640 | 981 | 32,104 | top holding 83%, unrealized 88% of PnL |
| 30 | theveeman | insider_or_allocation | 1,811,198 | 0.6x | 128,289 | 29% | 32% | -3,514 | 101,180 | 133,297 | -38,380 | sold $133,297 of tokens never bought on-chain |
| 31 | loganlim_x | skill_candidate | 1,771,414 | 0.2x | 118,013 | 67% | 38% | 103,131 | 741,026 | 222,426 | -144,876 | on-chain realized RH $741,026 (fully-priced tokens 7) / SOL $-144,876, sampled win rate 0.48 |
| 32 | bluntz_capital | skill_candidate | 1,649,387 | 0.2x | 31,380 | 22% | 35% | -11,046 | 563,734 | 388,251 | 379,986 | on-chain realized RH $563,734 (fully-priced tokens 6) / SOL $379,986, sampled win rate 0.48 |
| 33 | m0f0 | luck_one_bag | 1,646,900 | 1.0x | 6,212 | 89% | 35% | 42,552 | 1,247 | 0 | 1,502 | top holding 89%, unrealized 94% of PnL |
| 34 | Rowdy | kol_flow_mover | 1,571,898 | 0.2x | 169,198 |  |  | 23,911 | -10,463 | 117 | 91,563 | 169,198 followers |
| 35 | cryptochi3f_ | luck_one_bag | 1,449,230 | 1.1x | 5,358 | 82% | 24% | 19,246 | 255,245 | 10,620 | 29,804 | top holding 82%, unrealized 74% of PnL |
| 36 | justtesting | concentrated_bag | 1,408,320 | 0.7x | 8,465 | 52% | 11% | 67,929 | 771,164 | 0 |  | top holding 52% of portfolio |
| 37 | himgajria | active_churner_negative | 1,370,281 | 3.0x | 28,944 | 57% | 69% | -1,353,419 | 0 | 0 | 34,755 | sampled realized fomo -1353418.8, SOL realized 34754.863327 |
| 38 | Samisa_btc | concentrated_bag | 1,292,161 | 2.2x | 26,203 | 94% | 17% | -1,877 | -97 | 46 | 28,148 | top holding 94% of portfolio |
| 39 | cryptolyxe | active_churner_negative | 1,226,446 | 1.5x | 19,194 | 47% | 46% | -21,131 | 0 | 0 | -34,670 | sampled realized fomo -21131.314270000003, SOL realized -34670.21333448461 |
| 40 | Aurelius0121 | kol_flow_mover | 1,208,265 | 0.1x | 271,742 | 48% | 60% |  | 32,140 | 1,579 |  | 271,742 followers |
| 41 | NotARandomUser | concentrated_bag | 1,177,797 | 0.1x | 20,926 | 67% | 14% | 21,869 | 39,582 | 333 |  | top holding 67% of portfolio |
| 42 | TheGasChad | active_churner_negative | 1,171,101 | 1.0x | 5,025 | 53% | 22% | -795 | 97,520 | 0 | -62,812 | sampled realized fomo -795.1670576000026, SOL realized -62812.39719365855 |
| 43 | FartmanSacks | active_churner_negative | 1,169,683 | 1.7x | 39,273 | 40% | 33% | -28,301 | -16,921 | 1,026 | 1,569 | sampled realized fomo -28300.682610000007, SOL realized 1569.4819098505568 |
| 44 | SerAvocado | kol_flow_mover | 1,167,110 | 0.4x | 164,464 | 89% | 53% | 597,979 | -21,653 | 76 | -206,720 | 164,464 followers |
| 45 | insentos | luck_one_bag | 1,152,403 | 0.2x | 100,174 | 100% | 39% | -13,317 | 285,971 | 80 | 138,612 | top holding 100%, unrealized 110% of PnL |
| 46 | USronaldcarter | luck_one_bag | 1,095,445 | 0.2x | 23,972 | 81% | 37% | 104,369 |  | 0 | 89,388 | top holding 81%, unrealized 86% of PnL |
| 47 | Iknowwhyy | luck_one_bag | 1,091,853 | 0.6x | 19,621 | 81% | 51% | 76,053 | -15,459 | 0 | 9,980 | top holding 81%, unrealized 71% of PnL |
| 48 | LehmanFarters | luck_one_bag | 1,065,499 | 2.1x | 2,921 | 83% | 23% | 1,551 | 89,291 | 44,901 |  | top holding 83%, unrealized 86% of PnL |
| 49 | FullPinkYak | concentrated_bag | 1,052,002 | 0.5x | 3,118 | 50% | 31% | 63,982 | -10,660 | 47 | 37,912 | top holding 50% of portfolio |
| 50 | Visi235 | insider_or_allocation | 1,048,353 | 0.9x | 6,915 | 99% | 8% | 1,046,401 | 1,119,362 | 1,119,362 | 24,788 | sold $1,119,362 of tokens never bought on-chain |
| 51 | ethersole | concentrated_bag | 1,037,574 | 0.9x | 1,879 | 54% | 18% | -15,527 |  | 0 |  | top holding 54% of portfolio |
| 52 | carlwheezor | luck_one_bag | 1,037,297 | 0.5x | 10,625 | 99% | 26% | -745 | 933 | 0 |  | top holding 99%, unrealized 105% of PnL |
| 53 | crocsguy | luck_one_bag | 1,034,388 |  | 3,343 | 81% | 26% |  |  | 0 |  | top holding 81%, unrealized 96% of PnL |
| 54 | figaro | unknown | 1,028,936 | 0.5x | 6,272 |  |  |  | -30 | 0 | 64,102 |  |
| 55 | 397397 | luck_one_bag | 1,025,060 | 0.9x | 108,113 | 89% | 55% |  | 0 | 0 | 72,131 | top holding 89%, unrealized 98% of PnL |
| 56 | smol_intern | concentrated_bag | 1,014,257 | 0.1x | 59,515 | 85% | 8% |  | 5,898 | 0 |  | top holding 85% of portfolio |
| 57 | kingofgotham | luck_one_bag | 1,012,332 | 3.2x | 3,029 | 88% | 20% | -14,227 | -8,631 | 0 |  | PnL/volume 3.2x, top holding 88% of portfolio |
| 58 | workethic | luck_one_bag | 1,002,742 | 0.8x | 7,679 | 82% | 39% | -8,027 | -28,421 | 6,490 | -15,125 | top holding 82%, unrealized 106% of PnL |
| 59 | The__Solstice | insider_or_allocation | 964,373 | 0.4x | 110,128 | 50% | 53% | -71,763 | 622,909 | 566,243 | -33,302 | sold $566,243 of tokens never bought on-chain |
| 60 | pianches | active_churner_negative | 933,031 | 0.6x | 2,235 |  |  | -82,536 | 185,184 | 41,616 | 78,048 | sampled realized fomo -82536.2117703, SOL realized 78047.97030600003 |
| 61 | BumpyFancyCoral | luck_one_bag | 914,298 | 15.8x | 1,309 | 60% | 22% | -6,592 |  | 0 |  | PnL/volume 15.8x, top holding 60% of portfolio |
| 62 | paidinfullintel | concentrated_bag | 908,298 | 0.6x | 1,628 | 50% | 13% | 7,684 | -1,944 | 7 | -2,979 | top holding 50% of portfolio |
| 63 | montyMole44 | concentrated_bag | 906,778 | 1.7x | 2,625 | 62% | 18% | 2,221 | 53,865 | 0 | 901 | top holding 62% of portfolio |
| 64 | twaptops | luck_one_bag | 906,650 | 3.2x | 2,950 | 84% | 19% | -12,159 | 312,031 | 0 |  | PnL/volume 3.2x, top holding 84% of portfolio |
| 65 | iruletrenches | luck_one_bag | 899,365 | 0.6x | 14,775 | 77% | 64% | -12,180 | 8,422 | 8,609 | -11,927 | top holding 77%, unrealized 92% of PnL |
| 66 | Onchainmetrics | concentrated_bag | 869,503 | 0.8x | 8,626 | 67% | 22% |  | 203,346 | 752 | -7,659 | top holding 67% of portfolio |
| 67 | facap | unknown | 864,296 | 0.4x | 2,028 | 36% | 10% | 24,618 | 101,882 | 24 | 21,467 |  |
| 68 | fmpumpguy | luck_one_bag | 848,237 | 1.2x | 64,921 | 98% | 56% | -8,928 | 491 | 491 | -8,692 | top holding 98%, unrealized 106% of PnL |
| 69 | ventikohi | luck_one_bag | 814,799 | 1.2x | 4,304 | 78% | 22% | -76,024 | 58,671 | 0 | 65,046 | top holding 78%, unrealized 109% of PnL |
| 70 | GuavaGuy2001 | luck_one_bag | 812,363 | 1.2x | 21,899 | 90% | 44% | 2,321 | 0 | 0 | 262,531 | top holding 90%, unrealized 73% of PnL |
| 71 | CoinGurruu | luck_one_bag | 799,486 | 3.3x | 4,649 | 85% | 16% | -6,982 | 103,680 | 0 | -1,440 | PnL/volume 3.3x, top holding 85% of portfolio |
| 72 | Eagle_0X | luck_one_bag | 798,462 | 1.0x | 16,874 | 83% | 67% | -14,937 | 8,699 | 11,582 | -95,011 | top holding 83%, unrealized 112% of PnL |
| 73 | NachSOL | skill_candidate | 794,820 | 0.1x | 11,548 |  |  | -12,209 | 760,521 | 61,804 | -130,599 | on-chain realized RH $760,521 (fully-priced tokens 7) / SOL $-130,599, sampled win rate 0.4 |
| 74 | poker_kb_ | concentrated_bag | 793,219 | 2.7x | 1,966 | 75% | 22% | 5,447 | 940 | 0 | 241 | top holding 75% of portfolio |
| 75 | goosemanjones1 | luck_one_bag | 790,062 | 1.2x | 1,556 | 78% | 26% | -1,303 | 59,134 | 5,318 | 471 | top holding 78%, unrealized 95% of PnL |
| 76 | Pote_korea | luck_one_bag | 788,081 | 3.2x | 3,117 | 88% | 58% | 6,943 | 2,713 | 2,713 | -297 | PnL/volume 3.2x, top holding 88% of portfolio |
| 77 | MemeKingdom | unknown | 777,350 | 2.5x | 96,964 |  |  | -204 | 0 | 0 | -7,222 |  |
| 78 | sadcrissy | unknown | 775,782 | 0.2x | 39,839 | 46% | 16% |  | -10,697 | 0 | 34,152 |  |
| 79 | wileEcoyote | luck_one_bag | 749,726 | 0.3x | 1,965 | 95% | 19% | -78,625 | 178,680 | 506 | 10,221 | top holding 95%, unrealized 88% of PnL |
| 80 | Milliardi | luck_one_bag | 735,359 | 1.7x | 985 | 75% | 18% | -5,257 | 315 | 0 | 796 | top holding 75%, unrealized 100% of PnL |
| 81 | Tsukikage | active_churner_negative | 721,103 | 0.4x | 7,847 | 54% | 12% | -34,604 | -445 | 19 |  | sampled realized fomo -34603.8752981, SOL realized None |
| 82 | 0xleo | active_churner_negative | 717,447 | 0.0x | 63,498 | 49% | 18% | -74,643 | -58,194 | 0 | -11,404 | sampled realized fomo -74642.8656777, SOL realized -11403.864010839367 |
| 83 | Jols | luck_one_bag | 710,554 | 1.7x | 1,083 | 95% | 20% | -10,678 | 561 | 7 | 42,522 | top holding 95%, unrealized 101% of PnL |
| 84 | seralberttrades | active_churner_negative | 709,038 | 0.1x | 10,241 | 61% | 24% | -50,343 | -3,361 | 12,391 | 14,649 | sampled realized fomo -50343.39317799999, SOL realized 14648.619066012498 |
| 85 | XbtPika | active_churner_negative | 705,070 | 1.3x | 17,687 | 60% | 66% | -33,357 | 7,305 | 9,671 | 23,099 | sampled realized fomo -33357.131058, SOL realized 23098.64841501365 |
| 86 | byszzz | luck_one_bag | 701,187 | 6.1x | 1,543 | 99% | 32% | -12,046 | 0 | 0 | -5,304 | PnL/volume 6.1x, top holding 99% of portfolio |
| 87 | midcurver | active_churner_negative | 681,360 | 0.2x | 3,007 | 64% | 14% | -10,941 | 222,686 | 40,992 | -66,023 | sampled realized fomo -10941.006000000001, SOL realized -66022.77401135207 |
| 88 | boosteryting | active_churner_negative | 680,880 | 0.6x | 56,979 | 40% | 58% | -1,145 | 7 | 7 | -31,514 | sampled realized fomo -1145.3193218099998, SOL realized -31513.570354854448 |
| 89 | hungryghost | unknown | 664,042 | 1.8x | 2,620 |  |  |  | -863 | 0 | -24,283 |  |
| 90 | gundam | concentrated_bag | 651,399 | 0.8x | 1,057 | 56% | 11% | -5,455 | 70,086 | 0 | -13,112 | top holding 56% of portfolio |
| 91 | 0xdetweiler | skill_candidate | 649,717 | 0.1x | 12,002 | 40% | 25% | 40,782 | 85,944 | 1,719 |  | on-chain realized RH $85,944 (fully-priced tokens 11) / SOL $0, sampled win rate 0.4 |
| 92 | corleonefnf | luck_one_bag | 648,533 | 0.1x | 4,428 | 88% | 29% | -46,967 | 0 | 0 | -166,705 | top holding 88%, unrealized 99% of PnL |
| 93 | elliotrades | active_churner_negative | 642,257 | 1.0x | 4,188 | 72% | 17% | -29,494 | 0 | 0 |  | sampled realized fomo -29493.682999999997, SOL realized None |
| 94 | ImChizx | unknown | 634,894 | 0.3x | 12,247 | 44% | 24% |  | 949 | 111 |  |  |
| 95 | TheHappySwan | luck_one_bag | 632,654 | 0.1x | 1,489 | 84% | 25% | -89,539 | -10,152 | 190 | -54,553 | top holding 84%, unrealized 141% of PnL |
| 96 | alpinestar17 | active_churner_negative | 627,641 | 0.3x | 3,864 | 61% | 21% | 284,453 | 424,749 | 825 | -33,018 | sampled realized fomo 284453.12723, SOL realized -33018.40109786804 |
| 97 | NorthPraetor | luck_one_bag | 616,804 | 0.9x | 1,479 | 88% | 46% | 27,801 | 137,653 | 1,229 | -7,332 | top holding 88%, unrealized 77% of PnL |
| 98 | 81_tom | active_churner_negative | 607,829 | 0.4x | 1,628 |  |  |  | 44,189 | 161 | -44,867 | sampled realized fomo None, SOL realized -44866.51801600001 |
| 99 | WuKong365 | concentrated_bag | 605,598 | 0.2x | 11,953 | 71% | 23% | 646,691 | 49,169 | 33,859 |  | top holding 71% of portfolio |
| 100 | sockzt | luck_one_bag | 604,628 | 5.4x | 1,348 | 97% | 16% | -6,534 | -3,210 | 0 | -316 | PnL/volume 5.4x, top holding 97% of portfolio |
|  | jotagezin | luck_one_bag | 1,924,076 | 0.2x | 117,728 | 99% | 39% | -27,282 | -1,431 | 82 |  | top holding 99%, unrealized 90% of PnL |
|  | SpicyPeruvian_ | luck_one_bag | 913,420 | 0.2x | 3,652 | 82% | 25% | -27,079 | 45,984 | 279 | -205,667 | top holding 82%, unrealized 92% of PnL |
|  | Dxranteth | active_churner_negative | 828,088 | 0.2x | 54,286 | 66% | 19% | 54,162 | 3 | 0 | -128,476 | sampled realized fomo 54161.74908599996, SOL realized -128476.03769594422 |
|  | error | luck_one_bag | 600,383 | 0.0x | 1,018 | 86% | 13% | -3,729 | 7,172 | 4,907 | -9,690 | top holding 86%, unrealized 92% of PnL |
|  | Alexandar | concentrated_bag | 596,199 | 0.1x | 12,864 | 50% | 12% | 226,939 | 50,482 | 323 | -26,764 | top holding 50% of portfolio |
|  | smokey0x | luck_one_bag | 593,555 | 0.3x | 28,765 | 93% | 42% | -59,796 | 0 | 0 |  | top holding 93%, unrealized 106% of PnL |
|  | IssaTheCooker | luck_one_bag | 556,241 | 0.5x | 5,431 | 99% | 39% | -119,718 | 0 | 0 | -83,936 | top holding 99%, unrealized 111% of PnL |
|  | BigGoldPony | luck_one_bag | 553,896 | 0.4x | 902 | 99% | 19% | 56,552 |  | 0 |  | top holding 99%, unrealized 80% of PnL |
|  | derek518 | active_churner_negative | 552,864 | 0.4x | 484 | 41% | 12% | -31,561 | 47,175 | 0 | 0 | sampled realized fomo -31561.458737000004, SOL realized 0 |
|  | Binkieee | luck_one_bag | 538,920 | 0.0x | 147,244 | 87% | 52% |  | 73,177 | 50,834 |  | top holding 87%, unrealized 96% of PnL |
|  | fr3ak | active_churner_negative | 530,384 | 0.2x | 1,034 |  |  | -61,495 | 191,598 | 30 | -77,362 | sampled realized fomo -61495.121880000006, SOL realized -77361.735981 |
|  | gkisokay | unknown | 491,905 | 3.9x | 1,251 |  |  | -6,973 | 227,468 | 0 | -305 |  |
|  | SweetPriorCod | luck_one_bag | 490,013 | 1.3x | 529 | 100% | 25% | 42,072 |  | 0 |  | top holding 100%, unrealized 86% of PnL |
|  | naP0Liano | concentrated_bag | 488,350 | 2.5x | 1,610 | 86% | 0% | 533,094 |  | 0 |  | top holding 86% of portfolio |
|  | ericzhong | unknown | 486,327 | 0.1x | 4,599 | 16% | 10% |  | 44,217 | 31,915 |  |  |
|  | RunningClam | unknown | 461,115 | 0.6x | 2,633 | 46% | 24% |  | 5,007 | 11,866 |  |  |
|  | 0xdedrater | unknown | 459,299 | 0.0x | 10,031 | 30% | 18% |  | 255,470 | 243,518 |  |  |
|  | Y0u_andme | unknown | 459,245 | 0.6x | 2,644 |  |  |  | 4,159 | 5,226 |  |  |
|  | gweil0rd | luck_one_bag | 454,599 | 2.4x | 570 | 94% | 33% | -30,295 | -1,996 | 0 | 775 | top holding 94%, unrealized 104% of PnL |
|  | kv4rl | concentrated_bag | 343,740 | 0.2x | 1,910 | 64% | 0% | -8,003 | -2,316 | 0 | -21,803 | top holding 64% of portfolio |
|  | panceramic | active_churner_negative | 279,704 | 0.1x | 2,209 | 45% | 19% | -23,579 | 5,750 | 6,072 |  | sampled realized fomo -23578.531399999996, SOL realized None |
|  | ThePumponomics | luck_one_bag | 260,962 | 0.4x | 252 | 90% | 22% | -27,874 |  | 0 |  | top holding 90%, unrealized 125% of PnL |
|  | MoneyLord | luck_one_bag | 244,795 | 0.4x | 19,726 | 80% | 38% | -58,190 | -34,886 | 0 | -7,589 | top holding 80%, unrealized 232% of PnL |
|  | tummster | unknown | 204,566 | 0.1x | 412 | 23% | 12% | 56,487 |  | 0 |  |  |
|  | NoGiOlMoKiNi | luck_one_bag | 201,072 | 0.4x | 6,749 | 99% | 40% | -7,181 | -13,017 | 0 | 1,501 | top holding 99%, unrealized 252% of PnL |
|  | rasmr | unknown | 199,745 | 0.0x | 41,639 | 50% | 21% | 14,112 | 22,009 | 0 | 28,475 |  |
|  | proxy_ | active_churner_negative | 198,256 | 0.4x | 494 | 67% | 4% | -20,744 | 0 | 0 | -386 | sampled realized fomo -20743.996809999997, SOL realized -385.82200199999966 |
|  | pointfarmcap | luck_one_bag | 193,633 | 0.0x | 7,582 | 85% | 63% | -419 | 29,946 | 2,161 |  | top holding 85%, unrealized 295% of PnL |
|  | 0xExas | unknown | 183,686 | 0.7x | 250 | 32% | 29% | 24,092 |  | 0 |  |  |
|  | LuckyManRRR | luck_one_bag | 178,251 | 16.1x | 87 | 100% | 58% | -2,399 |  | 0 |  | PnL/volume 16.1x, top holding 100% of portfolio |
|  | memeking888 | luck_one_bag | 174,960 | 0.0x | 413 | 76% | 22% | 119,599 |  | 0 |  | top holding 76%, unrealized 133% of PnL |
|  | AnselFang | active_churner_negative | 172,473 | 0.1x | 761 | 40% | 17% | -66,707 | 156 | 156 |  | sampled realized fomo -66706.590526, SOL realized None |
|  | tikopumps | luck_one_bag | 171,583 | 0.1x | 2,553 | 100% | 38% | 150,398 | 0 | 0 | 142,795 | top holding 100%, unrealized 185% of PnL |
|  | CryptoTalkMan | active_churner_negative | 169,254 | 0.1x | 14,339 | 48% | 34% | -26,970 | 640 | 640 | 24,276 | sampled realized fomo -26969.808217, SOL realized 24275.886258485043 |
|  | The_Bogfather | concentrated_bag | 168,847 | 0.2x | 702 | 65% | 21% |  |  | 0 |  | top holding 65% of portfolio |
|  | GeorgeDroid | luck_one_bag | 167,548 | 0.1x | 145 | 93% | 41% | -81,049 |  | 0 | -49,032 | top holding 93%, unrealized 173% of PnL |
|  | Mirro7777 | concentrated_bag | 165,190 | 0.1x | 2,638 | 55% | 23% | 24,806 | 5 | 5 | -5,893 | top holding 55% of portfolio |
|  | vancute1112 | active_churner_negative | 159,084 | 0.3x | 1,020 | 71% | 11% | -40,183 | -2,094 | 261 | -7,880 | sampled realized fomo -40183.1882079, SOL realized -7879.787699691825 |
|  | 0xSisyphus | luck_one_bag | 158,028 | 0.6x | 3,196 | 80% | 29% | 5,465 |  | 0 |  | top holding 80%, unrealized 85% of PnL |
|  | vladsbutler | luck_one_bag | 157,663 | 0.5x | 138 | 100% | 14% | 8,518 |  | 0 |  | top holding 100%, unrealized 192% of PnL |
|  | 0xSporadic | active_churner_negative | 157,070 | 0.3x | 224 | 82% | 5% | -21,384 |  | 0 |  | sampled realized fomo -21383.61806838, SOL realized None |
|  | DipWheeler | unknown | 155,277 | 0.1x | 90,263 | 20% | 40% | -6,773 | 3,221 | 3,221 |  |  |
|  | B3NSS | luck_one_bag | 155,156 | 0.2x | 334 | 81% | 29% | -49,963 | 3,813 | 0 | 5,085 | top holding 81%, unrealized 98% of PnL |
|  | LowRivalRat | luck_one_bag | 152,042 | 0.2x | 1,018 | 97% | 14% | -46,551 | 84,572 | 0 | -18,422 | top holding 97%, unrealized 311% of PnL |
|  | BonerSqueeze | luck_one_bag | 147,425 | 0.1x | 1,188 | 84% | 22% | -52,952 |  | 0 |  | top holding 84%, unrealized 284% of PnL |
|  | colintrades1 | unknown | 143,815 | 0.2x | 455 | 42% | 6% |  | 139,128 | 93,274 | -9,223 |  |
|  | yeon__ | luck_one_bag | 141,679 | 0.1x | 4,931 | 81% | 31% | -38,552 |  | 0 |  | top holding 81%, unrealized 125% of PnL |