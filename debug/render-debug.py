# <pep8 compliant>
#
#   Addon Name: Render to Base64
#      Version: 1.1
#       Author: Your Name / AI Assistant
#  Description: Renders the current scene and copies the output image as a Base64 string to the clipboard.
#     Blender: 2.80, 2.90, 3.0, 4.0+
#    Location: Properties > Render Properties > Render to Base64
#     License: GPLv2+
#

bl_info = {
    "name": "Render to Base64",
    "author": "Your Name / AI Assistant",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "Properties > Render Properties > Render to Base64",
    "description": "Renders the scene and copies the image as Base64 to the clipboard.",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}

import bpy
import base64
import tempfile
import os
import traceback # For better error reporting

class SCENE_OT_render_to_base64(bpy.types.Operator):
    """Renders the scene and copies the image as Base64 to the clipboard"""
    bl_idname = "scene.render_to_base64"
    bl_label = "Render Scene to Base64 Clipboard"
    bl_options = {'REGISTER', 'UNDO'} # UNDO might not be strictly necessary but good practice

    # Optional property to choose format (can be added later)
    # output_format: bpy.props.EnumProperty(
    #     name="Format",
    #     description="Image format for temporary render",
    #     items=[('PNG', "PNG", "Lossless PNG format"),
    #            ('JPEG', "JPEG", "Lossy JPEG format")],
    #     default='PNG'
    # )

    def execute(self, context):
        scene = context.scene
        # Choose a format. PNG is generally good. JPEG is smaller but lossy.
        output_format = 'PNG'
        extension = output_format.lower()

        # Create a temporary file path
        # Using mkstemp for better control over file descriptor and deletion
        try:
            fd, temp_filepath = tempfile.mkstemp(suffix=f'.{extension}')
            os.close(fd) # Close the descriptor immediately, we just need the path
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create temporary file: {e}")
            return {'CANCELLED'}

        # --- Render and Save ---
        # We will render first, then save the 'Render Result' image
        # This avoids changing the scene's default render output path
        base64_string = None
        try:
            self.report({'INFO'}, "Starting render...")
            bpy.ops.render.render() # Renders to internal buffer 'Render Result'
            self.report({'INFO'}, "Render finished. Saving temporary image...")

            # Access the 'Render Result' image buffer
            img = bpy.data.images.get("Render Result")
            if not img:
                self.report({'ERROR'}, "Could not find 'Render Result' image after rendering.")
                if os.path.exists(temp_filepath): os.remove(temp_filepath) # Clean up temp file
                return {'CANCELLED'}

            # Temporarily set image save settings (important!)
            original_format = img.file_format
            original_filepath = img.filepath_raw # Store just in case, though we won't use it here
            img.file_format = output_format
            # Save the 'Render Result' image to the temporary path
            img.save_render(filepath=temp_filepath)

            # Restore original settings (optional but good practice)
            img.file_format = original_format
            # img.filepath_raw = original_filepath # Restore if needed

            self.report({'INFO'}, f"Temporary image saved to: {temp_filepath}")

            # --- Read, Encode, and Copy ---
            self.report({'INFO'}, "Reading image and encoding to Base64...")
            with open(temp_filepath, 'rb') as image_file:
                image_data = image_file.read()
                base64_bytes = base64.b64encode(image_data)
                base64_string = base64_bytes.decode('utf-8')

            if base64_string:
                context.window_manager.clipboard = base64_string
                img_size_info = f"({img.size[0]}x{img.size[1]}) " if img.size[0] > 0 else ""
                self.report({'INFO'}, f"Rendered {img_size_info}and copied Base64 ({len(base64_string)} chars) to clipboard.")
            else:
                 self.report({'WARNING'}, "Base64 encoding resulted in empty string.")

        except Exception as e:
            self.report({'ERROR'}, f"An error occurred: {e}")
            # Print detailed traceback to system console for debugging
            print("\n--- Render to Base64 Error ---")
            traceback.print_exc()
            print("------------------------------\n")
            return {'CANCELLED'}

        finally:
            # --- Clean up ---
            # Ensure the temporary file is deleted even if errors occurred
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                    # self.report({'INFO'}, f"Cleaned up temporary file: {temp_filepath}")
                except Exception as e_clean:
                    self.report({'WARNING'}, f"Could not remove temporary file {temp_filepath}: {e_clean}")

        return {'FINISHED'}


class RENDER_PT_render_to_base64(bpy.types.Panel):
    """Creates a Panel in the Render properties window"""
    bl_label = "Render to Base64"
    bl_idname = "RENDER_PT_render_to_base64"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render" # Put it in the Render Properties tab

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        # Draw the operator button
        row.operator(SCENE_OT_render_to_base64.bl_idname)

# --- Registration ---
classes = (
    SCENE_OT_render_to_base64,
    RENDER_PT_render_to_base64,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("Registered Render to Base64 Addon")


def unregister():
    for cls in reversed(classes): # Unregister in reverse order
        bpy.utils.unregister_class(cls)
    print("Unregistered Render to Base64 Addon")


# This allows you to run the script directly from Blender's Text editor
# to test the registration.
if __name__ == "__main__":
    # unregister() # Optional: Clean up previous registration if testing repeatedly
    register()