#!/bin/bash
# Omega Tensor Speed-Up Verification Script
# Targets: Load Average, Core Frequency, and Thermal Stability

clear
echo "==========================================="
echo "   JMD-OMEGA TELEMETRY: 8-CORE REVVL"
echo "==========================================="

while true; do
    # 1. Capture Load Average
    LOAD=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d',' -f1 | sed 's/ //g')
    
    # 2. Capture Real-Time Frequencies (Aggregated)
    # Note: On some Android kernels, /proc/cpuinfo is the most reliable source in proot
    AVG_FREQ=$(grep "cpu MHz" /proc/cpuinfo | awk '{sum+=$4} END {print sum/NR}')
    
    # 3. Capture Temperature (if thermal zone 0 is accessible)
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        TEMP=$(($(cat /sys/class/thermal/thermal_zone0/temp) / 1000))
    else
        TEMP="N/A"
    fi

    # 4. Display Results with Color Highlighting
    echo -e "\033[H" # Reset cursor to top
    echo -e "Current Load Avg: \033[1;32m$LOAD\033[0m (Target: 7.71)"
    echo -e "Avg Core Freq:    \033[1;36m$AVG_FREQ MHz\033[0m"
    echo -e "System Temp:      \033[1;31m$TEMP°C\033[0m"
    echo "-------------------------------------------"
    echo "Live Core Breakdown:"
    grep "cpu MHz" /proc/cpuinfo | awk '{printf "Core %d: %s MHz\n", NR-1, $4}'
    echo "==========================================="
    echo "Press [CTRL+C] to stop."
    
    sleep 1
done
