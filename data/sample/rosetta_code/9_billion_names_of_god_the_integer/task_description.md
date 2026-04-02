# 9 billion names of God the integer

This task is a variation of the short story by Arthur C. Clarke.
 
(Solvers should be aware of the consequences of completing this task.)

In detail, to specify what is meant by a &nbsp; “name”:
:The integer 1 has 1 name  &nbsp; &nbsp;  “1”.
:The integer 2 has 2 names &nbsp; “1+1”, &nbsp; and &nbsp; “2”.
:The integer 3 has 3 names &nbsp; “1+1+1”, &nbsp; “2+1”, &nbsp; and &nbsp; “3”.
:The integer 4 has 5 names &nbsp; “1+1+1+1”, &nbsp; “2+1+1”, &nbsp; “2+2”, &nbsp; “3+1”, &nbsp; “4”.
:The integer 5 has 7 names &nbsp; “1+1+1+1+1”, &nbsp; “2+1+1+1”, &nbsp; “2+2+1”, &nbsp; “3+1+1”, &nbsp; “3+2”, &nbsp; “4+1”, &nbsp; “5”.

;Task
Display the first 25 rows of a number triangle which begins:

                                      1
                                    1   1
                                  1   1   1 
                                1   2   1   1
                              1   2   2   1   1
                            1   3   3   2   1   1

Where row &nbsp; n &nbsp; corresponds to integer &nbsp; n, &nbsp; and each column &nbsp; C &nbsp; in row &nbsp; m &nbsp; from left to right corresponds to the number of names beginning with &nbsp; C.

A function &nbsp; G(n) &nbsp; should return the sum of the &nbsp; n-th &nbsp; row. 

Demonstrate this function by displaying: &nbsp; G(23), &nbsp; G(123), &nbsp; G(1234), &nbsp; and &nbsp; G(12345).  

Optionally note that the sum of the &nbsp; n-th &nbsp; row &nbsp; P(n) &nbsp; is the &nbsp;  [http://mathworld.wolfram.com/PartitionFunctionP.html &nbsp; integer partition function]. 

Demonstrate this is equivalent to &nbsp; G(n) &nbsp; by displaying: &nbsp; P(23), &nbsp; P(123), &nbsp; P(1234), &nbsp; and &nbsp; P(12345).

;Extra credit

If your environment is able, plot &nbsp; P(n) &nbsp; against &nbsp; n &nbsp; for &nbsp; n=1\ldots 999.

;Related tasks
* Partition function P
