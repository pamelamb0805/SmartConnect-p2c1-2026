
from rest_framework import serializers

from .models import Role, PersonRole, Credential, AccessRecord


class RoleSerializer(serializers.ModelSerializer):
    scope_display = serializers.CharField(
        source="get_scope_display",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Role
        fields = [
            "id_role",
            "name",
            "description",
            "scope",
            "scope_display",
            "status",
            "status_display",
        ]


class PersonRoleSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(
        source="person.__str__",
        read_only=True,
    )
    role_name = serializers.CharField(
        source="role.name",
        read_only=True,
    )
    terrain_name = serializers.CharField(
        source="terrain.name",
        read_only=True,
    )
    dwelling_name = serializers.CharField(
        source="dwelling.__str__",
        read_only=True,
    )

    class Meta:
        model = PersonRole
        fields = [
            "id_person_role",
            "person",
            "person_name",
            "role",
            "role_name",
            "start_date",
            "end_date",
            "status",
            "terrain",
            "terrain_name",
            "dwelling",
            "dwelling_name",
        ]

    def validate(self, attrs):
        instance = self.instance

        role = attrs.get(
            "role",
            instance.role if instance else None,
        )
        terrain = attrs.get(
            "terrain",
            instance.terrain if instance else None,
        )
        dwelling = attrs.get(
            "dwelling",
            instance.dwelling if instance else None,
        )
        start_date = attrs.get(
            "start_date",
            instance.start_date if instance else None,
        )
        end_date = attrs.get(
            "end_date",
            instance.end_date if instance else None,
        )

        if role:
            if role.scope == Role.Scope.TERRAIN:
                if not terrain or dwelling:
                    raise serializers.ValidationError({
                        "terrain": "El rol de terreno requiere un terreno y no admite una vivienda."
                    })

            elif role.scope == Role.Scope.DWELLING:
                if not dwelling or terrain:
                    raise serializers.ValidationError({
                        "dwelling": "El rol de vivienda requiere una vivienda y no admite un terreno."
                    })

                if terrain is None and dwelling:
                    pass

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "La fecha de término no puede ser anterior a la fecha de inicio."
            })

        return attrs

    def create(self, validated_data):
        instance = PersonRole(**validated_data)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.full_clean()
        instance.save()
        return instance


class CredentialSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(
        source="person.__str__",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Credential
        fields = [
            "id_credential",
            "uid_rfid",
            "status",
            "status_display",
            "person",
            "person_name",
        ]


class AccessRecordSerializer(serializers.ModelSerializer):
    access_point_name = serializers.CharField(
        source="access_point.name",
        read_only=True,
    )
    credential_uid = serializers.CharField(
        source="credential.uid_rfid",
        read_only=True,
    )
    person_name = serializers.SerializerMethodField()
    medium_display = serializers.CharField(
        source="get_medium_display",
        read_only=True,
    )
    result_display = serializers.CharField(
        source="get_result_display",
        read_only=True,
    )

    class Meta:
        model = AccessRecord
        fields = [
            "id_access_record",
            "date_time",
            "medium",
            "medium_display",
            "result",
            "result_display",
            "description",
            "uid_received",
            "access_point",
            "access_point_name",
            "credential",
            "credential_uid",
            "person_name",
        ]
        read_only_fields = ["date_time"]

    def get_person_name(self, obj):
        if obj.credential_id:
            return str(obj.credential.person)
        return None

    def validate(self, attrs):
        credential = attrs.get(
            "credential",
            self.instance.credential if self.instance else None,
        )
        uid_received = attrs.get(
            "uid_received",
            self.instance.uid_received if self.instance else "",
        )

        if credential and uid_received:
            if credential.uid_rfid != uid_received:
                raise serializers.ValidationError({
                    "uid_received": "El UID recibido no coincide con la credencial seleccionada."
                })

        return attrs



class AccessRequestSerializer(serializers.Serializer):
    uid_rfid = serializers.CharField(
        max_length=100,
        allow_blank=False,
        trim_whitespace=True,
    )

    access_point_id = serializers.IntegerField(
        min_value=1,
    )

    medium = serializers.ChoiceField(
        choices=[
            ("RFID", "RFID"),
            ("APP", "Aplicación"),
            ("OTRO", "Otro"),
        ],
    )
