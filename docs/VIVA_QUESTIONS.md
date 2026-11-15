# Viva Questions & Answers

1. **What is PySide6?**
It is the official Python module from the Qt for Python project, providing access to the complete Qt 6.0+ framework.

2. **Why use SQLite instead of MySQL?**
SQLite is serverless, requires no configuration, and stores data in a local file.

3. **What is a process vs a thread?**
A process is an executing program with its own memory space. A thread is a lightweight unit of execution within a process, sharing the same memory.

4. **What is a daemon/service?**
A background process that runs without direct user interaction, typically starting at boot.

5. **How does CSSA handle Windows vs Linux security differences?**
It uses the Adapter pattern. The core logic remains the same, but data collection relies on OS-specific adapters.

6. **What is the Principle of Least Privilege?**
Giving a user or process only the minimum access necessary to perform its required function.

7. **What is 0.0.0.0 vs 127.0.0.1?**
`0.0.0.0` binds to all available network interfaces (exposed). `127.0.0.1` binds only to the local loopback interface (local).

8. **What are SUID/SGID bits in Linux?**
Permissions that allow an executable to run with the privileges of the file owner or group.

9. **What is configuration drift?**
The phenomenon where system configurations gradually deviate from a known baseline over time.

10. **How does CSSA calculate the security score?**
It starts at 100 and subtracts points based on finding severity (e.g., -20 for Critical).

11. **What is an ACL?** 
Access Control List. It defines permissions for users/groups on a file or resource.

12. **TCP vs UDP?** 
TCP is connection-oriented and reliable, UDP is connectionless and fast.

13. **What is Systemd?** 
Linux init system and service manager used to bootstrap the user space and manage user processes.

14. **What is the Windows Registry?** 
Hierarchical database for Windows settings and configurations.

15. **User vs Kernel mode?** 
User mode has restricted access, kernel mode has unrestricted access to hardware.

16. **What is a false positive?** 
A secure configuration incorrectly flagged as a vulnerability.

17. **What is a false negative?** 
A vulnerability that the tool fails to detect.

18. **Why is this tool read-only?** 
To prevent accidental system damage during auditing and avoid being flagged as malware.

19. **What is an attack surface?** 
The total sum of vulnerabilities that can be exploited in a given system.

20. **How does the tool parse command output?** 
Using string manipulation, slicing, and regular expressions.

21. **What is PEP 8?** 
The Python style guide for writing readable code.

22. **What are Python Type Hints?** 
Annotations that indicate the expected data types for variables, arguments, and return values.

23. **What is a dataclass?** 
A decorator that automatically adds generated special methods like __init__ and __repr__ to classes.

24. **How do you handle exceptions in Python?** 
Using try/except/finally blocks to gracefully handle errors.

25. **What is a virtual environment?** 
An isolated Python environment that allows project-specific dependencies.

26. **What is pytest?** 
A robust testing framework for Python used for unit and integration testing.

27. **What is a mock in testing?** 
A fake object that simulates the behavior of a real object, useful for testing OS commands.

28. **What is fixture in pytest?** 
A function that provides a fixed baseline (data or state) upon which tests can reliably and repeatedly execute.

29. **What is the MIT license?** 
A permissive free software license allowing almost unrestricted use.

30. **How do you manage dependencies?** 
Using requirements.txt or pyproject.toml to specify exact versions of external libraries.

31. **What is an abstract base class?** 
A class that cannot be instantiated and defines an interface that subclasses must implement.

32. **How does `psutil` work?** 
It provides an interface for retrieving information on running processes and system utilization.

33. **What is a GUI event loop?** 
An infinite loop that waits for and dispatches events or messages (like clicks) in a program.

34. **What are Qt Signals and Slots?** 
A mechanism for communication between objects in Qt, e.g., connecting a button click to a function.

35. **What is MVC?** 
Model-View-Controller architecture, separating data, UI, and logic.

36. **How does the rule engine work?** 
It maps rule definitions to Python functions that evaluate system state and return findings.

37. **What is a baseline in security?** 
A documented, approved set of secure configurations used as a reference point.

38. **How do you detect the operating system in Python?** 
Using `platform.system()` which returns 'Windows', 'Linux', or 'Darwin'.

39. **What is a UID?** 
User Identifier in Linux, used to uniquely identify users.

40. **What is a GID?** 
Group Identifier in Linux, used to uniquely identify groups.

41. **What is root?** 
The superuser in Linux with absolute permissions over the system.

42. **What is Administrator?** 
The equivalent superuser in Windows with full system control.

43. **What is standard error (stderr)?** 
The standard output stream for error messages, separate from standard output (stdout).

44. **What is JSON?** 
JavaScript Object Notation, a lightweight data-interchange format used for rule definitions.

45. **Why use ReportLab?** 
It is a powerful library for generating high-quality PDFs dynamically in Python.
