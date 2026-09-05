from factorylens.session import MachineSession

session = MachineSession("cnc-03", "cnc_milling")

events = []
events.extend(session.trigger_operator_note())
events.append(session.set_job_context(material="S45C", process="finishing"))
events.append(session.machine_started())
events.append(session.machine_finished())

for event in events:
    print(event.to_json(indent=None))
