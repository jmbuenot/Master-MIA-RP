dim(5).
fill(1,3).
fill(2,3).
fill(0,2).
fill(3,2).
fill(4,2).

total(C,N) :- C= 0..4, #count{R : fill(R,C)} = N.