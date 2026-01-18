#ifndef SERIAL_READER_H
#define SERIAL_READER_H

#include <stdint.h>

#define NUM_UNITS 4

#pragma pack(push, 1)
struct drone_self_state {
    int16_t id;
    float lat;
    float lon;
    float alt;
    float velocity_north;
    float velocity_east;
    float velocity_down;
    float heading;
    int16_t sm_current_stat;
    int16_t battery_precentages;
    int16_t drones_keep_alive : NUM_UNITS; /* 4 bits member - MSB - unit 4..unit 1*/
    int16_t gps_3d_fix : 1; /* 1 bit fix */
    int16_t padding : 11; /* Padding to align to short (16 bits) if necessary, though pack(1) handles byte alignment. bitfields share the storage unit. 4+1=5 bits used. */
};
#pragma pack(pop)

#ifdef __cplusplus
extern "C" {
#endif

// Function prototype
// Returns 0 on success, -1 on error
int read_drone_state(int serial_fd, struct drone_self_state* state);

#ifdef __cplusplus
}
#endif

#endif // SERIAL_READER_H
