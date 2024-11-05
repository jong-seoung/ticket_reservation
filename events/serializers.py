from rest_framework import serializers


from accounts.serializers import AuthorSerializer
from events.models import Category, Event


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    @staticmethod
    def get_optimized_queryset():
        return Category.objects.all()
    

class EventSerializers(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
    
    @staticmethod
    def get_optimized_queryset():
        return Event.objects.all()
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    


class EventListSerializers(serializers.ModelSerializer):
    image = serializers.ImageField(source='profile.image', read_only=True)
    nickname = serializers.CharField(source='profile.nickname', read_only=True)

    category_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'image', 'nickname', 'category_name', 'price', 'event_date', 'created_at', 'period_start', 'period_end']
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None