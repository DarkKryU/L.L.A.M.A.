import shutil


def backupData():
    source = 'commodities.csv'
    backup = 'backup.csv'
    shutil.copy(source, backup)
    print(f"Backup of '{source}' created as '{backup}'.")


# backupData()

def restoreData():
    source = 'commodities.csv'
    backup = 'backup.csv'
    shutil.copy(backup, source)
    print(f"Restored backup of '{source}' from '{backup}'.")

restoreData()
