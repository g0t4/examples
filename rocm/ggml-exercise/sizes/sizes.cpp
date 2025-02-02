#include <iostream>

enum Color { red, green, blue };
enum Color8 : uint8_t { red8, green8, blue8 };

int main() {

  std::cout << "The size of an int is: " << sizeof(int) << std::endl;
  std::cout << "and an enum is : " << sizeof(Color) << std::endl;
  std::cout << "and uint8_t enum is : " << sizeof(Color8) << std::endl;

  return 0;
}
