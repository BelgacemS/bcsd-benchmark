  #include <stdio.h>

int main() {
    char s[5];  // Array to hold 4 characters + null terminator
    int result = 0;
    
    // Read the string
    scanf("%s", s);
    
    // Process each character
    for (int i = 0; i < 4; i++) {
        if (s[i] == '+') {
            result++;
        } else { // s[i] == '-'
            result--;
        }
    }
    
    // Output the result
    printf("%d\n", result);
    
    return 0;
}