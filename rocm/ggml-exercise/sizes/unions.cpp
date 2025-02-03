#include <iostream>

int main() {
    // an "either or" type ... you can access the same memory location with different types... but it all is backed by the same memory...
    //   so changing the integer would alter the char(s) and float, etc
    union Data {
        int i; // size: 4
        uint ui;
        float f;  // size: 4 https://en.wikipedia.org/wiki/Single-precision_floating-point_format
        char str; // size: 1
        /*char str[20];*/
        char strfour[4]; // size: 4
        // bool bits[8]; // size: 8 (bytes)
    };

    union Data data;

    data.i = 49;
    /*data.i = 12593; // 0x3131 (bits) => 0x31 == 49 == ascii '1' (btw use your `bitmaths 0x3131`)... so we get ascii "11"*/
    // data.str = 48 => ascii "0"
    // data.str = 49 => ascii "1"
    // data.str = 49 =>
    //
    //    float 0x0 (sign bit)
    //    0x0000 0000 (8 exponent bits) ==> encodes for 2^-126 (not 2^0)
    //    0x000 0000  0000 0000  0011 0001 23bit (significand/mantissa)
    //      so to convert to base 10 which is what float is printed in:
    //      (2^-23 + 2^-19 + 2^-18)*2^-126  = 6.86636248e-44 ==> 6.87e-44 (base 10)

    std::cout << "i (int): " << data.i << " - size: " << sizeof(data.i) << std::endl;
    std::cout << "ui (uint): " << data.ui << " - size: " << sizeof(data.ui) << std::endl;
    std::cout << "str (char): '" << data.str << "' - size: " << sizeof(data.str) << std::endl;
    std::cout << "f (float): " << data.f << " - size: " << sizeof(data.f) << std::endl;
    std::cout << "strfour (char[4]): '" << data.strfour << "' - size: " << sizeof(data.strfour) << std::endl;



    union Data other;

    // use integer field to encode "wes" in ascii

    // backwards FYI: shows as "sew"
    other.i = 7824755; // bitmaths 0x776573
    /*const char *wes = "wes";*/
    /*other.i = (wes[0] << 16) | (wes[1] << 8) | wes[2];*/
    std::cout << std::endl << std::endl << "other:" << std::endl;
    std::cout << "data.i: " << other.i << std::endl;
    std::cout << "data.ui: " << other.ui << std::endl;
    std::cout << "strfour: " << other.strfour << std::endl;
}
