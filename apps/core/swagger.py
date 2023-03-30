from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors import SwaggerAutoSchema

def get_summary(string):
    if string is not None:
        result = string.strip().replace(" ", "").split("\n")
        return result[0]


class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        tags = super().get_tags(operation_keys)
        # if "api" in tags and operation_keys:
        #     print(operation_keys)
        #     tags[0] = operation_keys[settings.SWAGGER_SETTINGS.get('AUTO_SCHEMA_TYPE', 2)]
        # tags=summary = [get_summary(self.__dict__.get('view').__doc__)]
        return tags

    def get_summary_and_description(self):
        summary_and_description = super().get_summary_and_description()
        summary = get_summary(self.__dict__.get('view').__doc__)
        description = summary_and_description[1]
        if description == summary:
            if self.__dict__.get("method") == "GET":
                description = "获取"
            elif self.__dict__.get("method") == "POST":
                description = "新增"
        if summary is not None and description is not None:
            summary = summary+"-"+description
        return summary, description


class CustomOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        """Generate a :class:`.Swagger` object with custom tags"""
        swagger = super().get_schema(request, public)
        swagger.tags = [
            {
                "name": "auth",
                "description": "授权相关",
            },
            {
                'name': 'users',
                'description': '用户相关'
            },
            {
                'name': 'servers',
                'description': '服务器相关'
            },
        ]
        swagger.schemes = ["http", "https"]

        return swagger
