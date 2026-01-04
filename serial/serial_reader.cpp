#include "serial_reader.h"
#include <unistd.h>
#include <errno.h>
#include <iostream>
#include <cstring>

/**
 * Reads a drone_self_state struct from the given serial file descriptor.
 * This function blocks until the full size of the struct is read or an error occurs.
 * 
 * @param serial_fd File descriptor for the serial port
 * @param state Pointer to the struct where data will be stored
 * @return 0 on success, -1 on failure
 */
int read_drone_state(int serial_fd, struct drone_self_state* state) {
    if (state == nullptr) {
        return -1;
    }

    size_t total_read = 0;
    size_t size_to_read = sizeof(struct drone_self_state);
    uint8_t* buffer = reinterpret_cast<uint8_t*>(state);

    while (total_read < size_to_read) {
        ssize_t bytes_read = read(serial_fd, buffer + total_read, size_to_read - total_read);

        if (bytes_read < 0) {
            // Error occurred
            if (errno == EINTR) {
                // Interrupted system call, retry
                continue;
            }
            std::cerr << "Error reading from serial: " << strerror(errno) << std::endl;
            return -1;
        } else if (bytes_read == 0) {
            // EOF reached (connection closed) before full struct read
            std::cerr << "Serial connection closed unexpectedly." << std::endl;
            return -1;
        }

        total_read += bytes_read;
    }

    return 0;
}

// Example usage / test main
#ifdef TEST_MAIN
#include <fcntl.h>

int main() {
    // Just a mock main to demonstrate compilation. 
    // In a real scenario, you'd open a real serial port device (e.g., /dev/ttyUSB0)
    std::cout << "Compiling successfully. Size of struct: " << sizeof(struct drone_self_state) << std::endl;
    return 0;
}
#endif
