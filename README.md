# Very basic custom component for receiving SNMP traps

## Prepare

Add/download to your HA config directory

- Ensure you know where your `config` directory is
- Create a `custom_components` directory if it doesn't exist yet
- Make sure `snmptrap` is a directory in there with all of these files in it

## Add to your Home Assistant installation

- Restart your Home Assitant
- Go to devices
- Click the Add Integration button
- Search for SNMP Trap and add it
- "That's all folks"

## Example automation

```yaml
alias: SNMPTrap test
description: ""
triggers:
  - trigger: state
    entity_id: sensor.snmp_last_trap
conditions: []
actions:
  - action: notify.send_message
    metadata: {}
    target:
      device_id: aeeed3b0766fb637148060d7bfbee77b
    data:
      title: SNMP Trap received
      message: |
        Trap details: {% for k, v in trigger.to_state.attributes.kv.items() %}
          {{ k }} → {{ v }}
        {% endfor %}
mode: single
```

## Example trap sending

Nothing real life here, just when you have a Linux system with `snmptrap` installed (i.e. `sudo apt install snmp` for Ubuntu)

`snmptrap -v2c -c public ip.addr.of.ha "" 1.3.6.1.4.1.8072.2.3.0.1 1.3.6.1.4.1.8072.2.3.0.1 s "test2  bla^Mothertest with some  value^Manother with int  7"`

Which demos one of the potential scenarios and will actively split lines (with any `\r`/`\n` combinations) and make key/value pairs of anything with multiple spaces.
