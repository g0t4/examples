#include <iostream>

enum Color {
  red,
  green,
  blue
};
enum Color8 : uint8_t {
  red8,
  green8,
  blue8
};

int main() {

  std::cout << "The size of an int is: " << sizeof(int) << std::endl;
  std::cout << "The size of a short int is: " << sizeof(short int) << std::endl;

  std::cout << "The size of a long int is: " << sizeof(long int) << std::endl;

  std::cout << "The size of a long long int is: " << sizeof(long long int) << std::endl;

  std::cout << "The size of a double is: " << sizeof(double) << std::endl;

  // char type is signed by default
  std::cout << "The size of a char is: " << sizeof(char) << std::endl;

  // unsigned data types are

  std::cout << "and an enum is : " << sizeof(Color) << std::endl;
  std::cout << "and uint8_t enum is : " << sizeof(Color8) << std::endl;

  return 0;
}
