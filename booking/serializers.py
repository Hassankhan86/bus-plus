from rest_framework import serializers
from booking.models import *
from .CONSTANT import *
from django.conf import settings
from .utils import parse_return_time_and_date, is_valid_self_drive_schedule


class CitiesSerializers(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    class Meta:
        model = Cities
        fields = "__all__"


class StopsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stops
        fields = "__all__"


class InsurancesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insurance
        fields = "__all__"


class RouteSerializer(serializers.ModelSerializer):
    bus_stops = StopsSerializer(required=False, many=True)

    class Meta:
        model = Route
        fields = "__all__"


class TripSerializer(serializers.ModelSerializer):
    routes = serializers.SerializerMethodField()
    total_stops = serializers.SerializerMethodField()
    total_passengers = serializers.SerializerMethodField()
    on_trip_direction = serializers.SerializerMethodField()
    trip_total_distance = serializers.SerializerMethodField()
    routes_price = serializers.SerializerMethodField()
    routes_stop_charges_price = serializers.SerializerMethodField()
    trip_tax = serializers.SerializerMethodField()
    service_charge = serializers.SerializerMethodField()
    sub_total = serializers.SerializerMethodField()
    trip_charges = serializers.SerializerMethodField()

    def get_routes(self, obj):
        routes = obj.routes.all()
        return RouteSerializer(routes, many=True, required=False).data

    def get_total_stops(self, obj):
        return obj.get_total_stops()

    def get_total_passengers(self, obj):
        return obj.get_total_passengers()

    def get_on_trip_direction(self, obj):
        return obj.get_on_trip_direction()

    def get_trip_total_distance(self, obj):
        return obj.get_trip_total_distance()

    def get_routes_price(self, obj):
        return obj.get_routes_price()

    def get_routes_stop_charges_price(self, obj):
        return obj.get_routes_stop_charges_price()

    def get_trip_tax(self, obj):
        return obj.get_trip_tax()

    def get_service_charge(self, obj):
        return obj.get_service_charge()

    def get_sub_total(self, obj):
        return obj.get_sub_total()

    def get_trip_charges(self, obj):
        return obj.get_trip_charges()

    class Meta:
        model = Trip
        fields = "__all__"


class TripCreateSerializer(serializers.Serializer):
    selectedBusIds = serializers.CharField(required=False)
    pickup_lat = serializers.CharField()
    pickup = serializers.CharField()
    pickup_long = serializers.CharField()
    destination_lat = serializers.CharField()
    destination_long = serializers.CharField()
    destination = serializers.CharField()
    pickup_date = serializers.DateField(format="%d-%m-%Y")
    drop_off_date = serializers.DateField(required=False, format="%d-%m-%Y")
    return_date = serializers.DateField(required=False, format="%d-%m-%Y")
    drop_off_time = serializers.CharField(required=False)
    pickup_time = serializers.CharField()
    return_pickup_time = serializers.CharField(required=False)
    total_distance = serializers.CharField()
    estimated_time = serializers.CharField(default="0h 0m")
    total_distance_in_number = serializers.CharField(default=0)
    trip_type = serializers.IntegerField(default=1)

    def to_representation(self, instance):
        representation = super(self).to_representation(instance)
        representation['drop_off_date'] = instance.drop_off_date.strftime("%Y-%m-%d")
        representation['return_date'] = instance.return_date.strftime("%Y-%m-%d")
        representation['pickup_date'] = instance.pickup_date.strftime("%Y-%m-%d")
        return representation

    def validate(self, attrs):

        destination_location = attrs.get("destination", "")
        pickup_location = attrs.get("pickup", "")
        pickup = pickup_location.split(" ")[0]
        destination = destination_location.split(" ")[0]
        if not destination_location or not pickup:
            raise serializers.ValidationError("Pickup and destination are required")
        selectedBusIds = int(attrs.get('selectedBusIds', 0))
        trip_type = attrs.get("trip_type", 1)
        if trip_type == "3" or trip_type == 3:
            bus = Bus.objects.filter(id=selectedBusIds).first()
            if bus:
                if not bus.self_drive_available:
                    raise serializers.ValidationError("this bus is not available for self drive")
                if not bus.is_available:
                    raise serializers.ValidationError("Bus is not available for drive please select another one")
            else:
                raise serializers.ValidationError("Invalid bus selected! please try with another bus")
            parsed_date = parse_str_date_time(attrs.get("pickup_date", ""), attrs.get("pickup_time", ""))
            status, message = is_valid_self_drive_schedule(parsed_date)
            if not status:
                raise serializers.ValidationError(message)
            pickup = settings.SELF_DRIVE_PICKUP_ADDRESS
            destination = settings.SELF_DRIVE_PICKUP_ADDRESS
        if trip_type != 3 and pickup_location == destination_location:
            raise serializers.ValidationError("Pickup and destination cannot be same")
        pickup = pickup.strip()
        destination = destination.strip()
        pickup_instance = Cities.objects.filter(city__icontains=pickup, is_active=True).first()
        destination_instance = Cities.objects.filter(city__icontains=destination, is_active=True).first()
        if not pickup_instance and pickup_location != settings.SELF_DRIVE_PICKUP_ADDRESS:
            raise serializers.ValidationError(f"We are not proving services on {pickup}")
        if not destination_instance and destination_location != settings.SELF_DRIVE_PICKUP_ADDRESS:
            raise serializers.ValidationError(f"We are not proving services on {destination}")

        if trip_type == 3:
            pickup_date = parse_str_date_time(attrs.get("pickup_date"), attrs.get("pickup_time"))
            return_date = parse_str_date_time(attrs.get("drop_off_date"), attrs.get("drop_off_time"))
            if return_date < pickup_date:
                raise serializers.ValidationError("Return date must be after pickup time")
        if trip_type == 2:
            return_date = attrs.get("return_date")
            drop_off_date = attrs.get("drop_off_date")
            if return_date and return_date < drop_off_date:
                raise serializers.ValidationError("Return date must be after drop off date")
        return attrs

    def create(self, validated_data):
        show_buses = settings.IS_BUSES_SHOW_TO_USER
        selectedBusIds = int(validated_data.get('selectedBusIds', 0))
        pickup_lat = validated_data.get('pickup_lat', "").strip()
        pickup = validated_data.get('pickup', "").strip()
        pickup_long = validated_data.get('pickup_long', "").strip()
        destination_lat = validated_data.get('destination_lat', "").strip()
        destination_long = validated_data.get('destination_long', "").strip()
        destination = validated_data.get('destination', "").strip()
        on_going_date = validated_data.get('pickup_date')
        pickup_time = validated_data.get('pickup_time')
        return_pickup_time = validated_data.get('return_pickup_time')
        drop_off_time = validated_data.get('drop_off_time')
        drop_off_date = validated_data.get('drop_off_date')
        return_date = validated_data.get('return_date', "")
        total_distance = validated_data.get('total_distance', "").strip()
        estimated_time = validated_data.get('estimated_time', "").strip()
        trip_type = validated_data.get('trip_type', 1)
        total_distance_in_number = validated_data.get('total_distance_in_number', "").strip()

        return_drop_off_time = parse_return_time_and_date(return_pickup_time, return_date, estimated_time)
        is_two_way_trip = False if trip_type == 2 else True

        is_driver_required = True
        scale = BUS_CHARGES_SCALE[1][0]
        scale_charge = 1
        if trip_type == "3" or trip_type == 3:
            pickup = settings.SELF_DRIVE_PICKUP_ADDRESS
            destination = settings.SELF_DRIVE_PICKUP_ADDRESS
            is_driver_required = False
        bus = None
        try:
            trip_type = TRIP_TYPE[trip_type - 1][0]
        except:
            trip_type = TRIP_TYPE[0][0]
        charges_type = BUS_CHARGES_SCALE[0][0]
        if trip_type != TRIP_TYPE[2][0]:
            charges_type = BUS_CHARGES_SCALE[1][0]
        if show_buses or trip_type == TRIP_TYPE[2][0]:
            bus = Bus.objects.filter(id=selectedBusIds).first()
            scale_bus = bus.bus_charges.filter(scale=charges_type).first()
            if scale_bus:
                scale = scale_bus.scale
                scale_charge = scale_bus.per_scale_charges
            else:
                scale = BUS_CHARGES_SCALE[0][1]
                scale_charge = 0

        trip = Trip.objects.create(
            bus=bus,
            on_going_date=on_going_date,
            return_date=return_date if is_two_way_trip else None,
            is_driver_required=is_driver_required,
            trip_type=trip_type,
            scale=scale,
            per_scale_charges=scale_charge
        )

        route = Route.objects.create(
            trip=trip,
            route_type=ROUTE_TYPES[0][0],
            departure_latitude=pickup_lat,
            departure_longitude=pickup_long,
            departure_city=pickup,
            total_distance_in_km=total_distance_in_number,
            destination_latitude=destination_lat,
            destination_longitude=destination_long,
            destination_city=destination,
            total_distance=total_distance,
            estimated_time=estimated_time,
            pickup_date=on_going_date,
            pickup_time=pickup_time,
            drop_off_time=drop_off_time,
            drop_off_date=drop_off_date,
        )
        if is_two_way_trip:
            return_route = Route.objects.create(
                trip=trip,
                route_type=ROUTE_TYPES[1][0],
                departure_latitude=destination_lat,
                departure_longitude=destination_long,
                departure_city=destination,
                destination_latitude=pickup_lat,
                destination_longitude=pickup_long,
                destination_city=pickup,
                total_distance=total_distance,
                estimated_time=estimated_time,
                total_distance_in_km=total_distance_in_number,
                pickup_date=return_date,
                pickup_time=return_pickup_time,
                drop_off_time=return_drop_off_time,
                drop_off_date=drop_off_date,

            )
        return trip


class StopsListSerializer(serializers.Serializer):
    location = serializers.CharField()
    number_of_mint = serializers.IntegerField()


class BusImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusImages
        fields = '__all__'
