# ✈️ Travel Tracker

> Turn travel confirmation emails into Home Assistant entities.

Travel Tracker is a Home Assistant custom integration that automatically scans your travel confirmation emails and builds structured trip information for use in dashboards, automations, notifications, and family travel planning.

Instead of manually entering flights, hotels, and rental cars into Home Assistant, simply book your travel and let Travel Tracker do the rest.

---

## ✨ Planned Features

### ✈️ Flights

- Flight number
- Airline
- Departure airport
- Arrival airport
- Departure time
- Arrival time

### 🏨 Hotels

- Hotel name
- City
- Check-in date
- Check-out date

### 🚗 Rental Cars

- Rental company
- Pickup location
- Pickup date
- Return date

### 📅 Trip Management

- Automatically group reservations into trips
- Next trip summary
- Days until departure
- Family-friendly travel dashboard
- Home Assistant entities
- Automation support

---

# Supported Providers (Planned)

## Airlines

- American Airlines
- Delta
- United
- Southwest
- JetBlue
- Air Canada

## Hotels

- Hilton
- Marriott

## Rental Cars

- National
- Enterprise

Additional providers will be added over time.

---

# Example Dashboard

```
✈️ NEXT TRIP

Dallas, Texas

Leaves
July 22

Flight
AA1234

Hotel
Hilton Garden Inn

Rental Car
National

Returns
July 25
```

---

# Planned Home Assistant Entities

```
sensor.next_trip
sensor.next_flight
sensor.next_hotel
sensor.next_rental_car

binary_sensor.travel_today
binary_sensor.travel_this_week
sensor.days_until_trip
```

---

# Privacy & Security

Travel Tracker is designed with privacy as a first-class feature.

- ✅ All email processing happens locally inside Home Assistant.
- ✅ No cloud services are used.
- ✅ No travel data leaves your Home Assistant instance.
- ✅ Confirmation numbers are **not stored**.
- ✅ Ticket numbers are **not stored**.
- ✅ Payment information is **never stored**.
- ✅ Loyalty account numbers are **never stored**.
- ✅ Reservation management links are discarded after parsing.

Travel Tracker stores only the information necessary to build your travel dashboard and Home Assistant entities.

---

# Roadmap

## Version 0.1

- Rename integration
- Standalone Home Assistant integration
- Development environment

## Version 0.2

- American Airlines parser

## Version 0.3

- Hilton parser

## Version 0.4

- National Car Rental parser

## Version 0.5

- Trip Builder

## Version 0.6

- Dashboard entities

## Version 1.0

- HACS Release
- Community provider support

---

# Credits

Travel Tracker began as a fork of the outstanding **Mail and Packages** integration created by **Moralmunky** and its contributors.

The Mail and Packages project solved the challenge of securely connecting Home Assistant to email providers and building a robust email-processing framework. Travel Tracker builds upon that foundation to parse travel confirmations instead of shipment notifications.

A sincere thank you to:

- **Moralmunky**
- **@firstof9**
- All contributors to the Mail and Packages project

Their work made this project possible.

Original Project:

https://github.com/moralmunky/Home-Assistant-Mail-And-Packages

---

# Contributing

Contributions, bug reports, provider requests, and feature ideas are always welcome.

As the project grows, additional airline, hotel, rental car, cruise, rail, and travel providers will be added with community support.

---

# License

This project is licensed under the MIT License.

Travel Tracker is a derivative work of the Mail and Packages integration and retains all required license notices from the original project.ns)
