#include <windows.h>
#include <iostream>

int Sum(int a, int b) {
    return a + b;
}

int main() {
    std::cout << "Hello from test_input!" << std::endl;

    int result = Sum(5, 7);
    std::cout << "Sum = " << result << std::endl;

    if (result > 10) {
        std::cout << "Result is greater than 10." << std::endl;
    } else {
        std::cout << "Result is 10 or less." << std::endl;
    }

    return 0;
}
