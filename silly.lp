dim(5).
fill(0,1).
fill(1,0).
fill(1,1).
fill(1,2).


total(C,N):- #count{R: fill(R,C)} = N, C= 0..3.