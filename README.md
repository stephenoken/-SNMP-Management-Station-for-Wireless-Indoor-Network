[![Stories in Ready](https://badge.waffle.io/stephenoken/-SNMP-Management-Station-for-Wireless-Indoor-Network.png?label=ready&title=Ready)](https://waffle.io/stephenoken/-SNMP-Management-Station-for-Wireless-Indoor-Network)
# -SNMP-Management-Station-for-Wireless-Indoor-Network

## Project Dependancies
- `Brew install libsmi`
- `Brew install net-snmp`

## Run example script
- `python src/pysnmp_example.py`
- `snmpwalk -v2c -c public 127.0.0.1 .1.3.6.1.2` 

## Run system
- In root of `src` folder
- Run each of the follwing commands in a sperate terminal session
- `python sensors/thermometer.py`
- `python src/snmp_components/agent.py`
- `python src/sample_scripts/snmp_get.py`

## Useful Materials
- <a href="http://gzsl.lzu.edu.cn/pysnmp/pysnmp-tutorial.html">PYSNMP Tutorial</a>

##Order of Execution


- Thermometer
- Thermometer Agent
- Heater
- Heater Agent
- manager
- Lights Agent

