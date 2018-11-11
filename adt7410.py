import smbus

TEMP_MSB_REG      = 0x00
TEMP_LSB_REG      = 0x01
STATUS_REG        = 0x02
CONFIGURATION_REG = 0x03
WHO_AM_I_REG      = 0x0B

BIT13_RESOLUTION      = 0x00
BIT16_RESOLUTION      = 0x80

OP_MODE_CONTINUOUS    = 0x00
OP_MODE_ONESHOT       = 0x20
OP_MODE_SPS           = 0x40
OP_MODE_SHUTDOWN      = 0x60

INTERRUPT_MODE        = 0x00
COMPARATOR_MODE       = 0x10

INT_LOW               = 0x00
INT_HIGH              = 0x08

CT_LOW                = 0x00
CT_HIGH               = 0x04

BIT16_OP_MODE_1FAULT  = 0x00
BIT16_OP_MODE_2FAULT  = 0x01
BIT16_OP_MODE_3FAULT  = 0x02
BIT16_OP_MODE_4FAULT  = 0x03

SLAVE_ADDRESS     = 0x48

class ADT7410(object):

    ## Constructor
    #  @param [in] address ADT7410 I2C slave address default:0x48
    def __init__(self, bus, address=SLAVE_ADDRESS):
        self.address = address
        self.bus = bus
        self.configure()

    ## Configure Device
    def configure(self):
        conf = BIT16_RESOLUTION | BIT16_OP_MODE_1FAULT | CT_LOW | INT_LOW | INTERRUPT_MODE | OP_MODE_CONTINUOUS
        print('Configure ADR7410')
        self.bus.write_byte_data(self.address, CONFIGURATION_REG, conf)
        print('Configuration complete')

    ## Data Ready Check
    #  @retval true Data ready
    #  @retval false Data Not ready
    def checkDataReady(self):
        status = self.bus.read_byte_data(self.address, STATUS_REG)

        if status & 0x80:
            return False
        else:
            return True

    ## Read Temperature Data
    #  @return value Temperature Data
    def read(self):
        if self.checkDataReady():
            config = self.bus.read_byte_data(self.address, CONFIGURATION_REG)
            data = self.bus.read_i2c_block_data(self.address, TEMP_MSB_REG, 2)

            adc = (data[0] << 8) | data[1]
            val = adc

            if config & BIT16_RESOLUTION:
                # 16bit resolution
                if adc & 0x8000:
                    val = val - 65536
                temp = float(val / 128.0)

            else:
                # 13bit resolution
                adc >>= 3
                if adc & 0x1000:
                    val = val - 8192
                temp = float(val / 16.0)

            return temp

        else:
            return 0.0
