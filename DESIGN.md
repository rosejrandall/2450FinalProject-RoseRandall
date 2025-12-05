The system uses an MVC pattern where the model is the classes, the view is the menus, and the controller is a booking manager class.

The major classes in the system:
Class        |    Description                        |  Key Attributes
Client       |     Represents a salon customer.      |  client_id, name, phone.
Technician   |     Represents a nail professional.   |   tech_id, name, availability (dict), schedule (dict).
Appointment  |  A booking instance linking a client and technician to a specific service. |  appt_id, date, time, client (obj), technician (obj), service, price, status.

The controller:
BookingManager  | The central controller and data repository. Manages all dictionaries (clients, technicians, appointments), handles ID generation, implements all business logic (booking, cancellation), and manages persistence (I/O).

Throughout the process I learned that planning ahead is very helpful, but can be difficult to do when it's not clear how different systems might work best and how they'll work together. Some changes I would make include a better schedule graphic interface for the users. This is difficult to do in a menu view, but would likely look better using something like tkinter. Overall, I would spend a bit more time planning and potentially researching more efficient ways that similar booking systems have been created.


