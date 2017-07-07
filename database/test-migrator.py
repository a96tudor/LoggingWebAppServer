from database_handler import DatabaseHandler as DH

dh = DH("SMU-logs.db")

print(dh.get_logs())
print(dh.get_working_users())