% Thermometer puzzle encoding.
% Select for each cell whether it is filled with mercury.
{ fill(R,C) } :- cell(R,C).

% Expose the grid dimension expected by decode.py.
dim(n).

% Track which indexed segment of a thermometer is filled.
filled_index(BR,BC,I) :- thermo_cell(BR,BC,I,R,C), fill(R,C).
%I represent the index of the cell at the thermometer
%BR and BC represent the row and column for the bulb of the thermometer, identifying the proper thermometer
% R and C represent the column of the cell of the thermometer


% A segment can only be filled if all previous segments of its thermometer are filled.
:- thermo_cell(BR,BC,I,R,C), I > 1, fill(R,C), not filled_index(BR,BC,I-1).

% Each row must match its target count of filled cells.
:- row_target(R,M), #count{C : fill(R,C)} != M.

% Each column must match its target count of filled cells.
:- col_target(C,M), #count{R : fill(R,C)} != M.

#show fill/2.