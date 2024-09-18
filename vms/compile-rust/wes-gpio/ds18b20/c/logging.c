#if LOG_LEVEL >= 1
#define LOG_INFO(fmt, ...) printf("INFO: " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_INFO(fmt, ...)
#endif

#if LOG_LEVEL >= 2
#define LOG_DEBUG(fmt, ...) printf("DEBUG: " fmt "\n", ##__VA_ARGS__)
#else
#define LOG_DEBUG(fmt, ...)
#endif

#define LOG_ERROR(fmt, ...) fprintf(stderr, "ERROR: " fmt "\n", ##__VA_ARGS__)