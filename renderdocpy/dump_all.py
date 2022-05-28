# RenderDoc Python console, powered by python 3.9.7.
# The 'pyrenderdoc' object is the current CaptureContext instance.
# The 'renderdoc' and 'qrenderdoc' modules are available.
# Documentation is available: https://renderdoc.org/docs/python_api/index.html

import os

context = pyrenderdoc
replay_manager = context.Replay()


def dump_shader_contents(shader, outfile):
    shader_reflection = shader.reflection
    debug_info = shader_reflection.debugInfo

    assert len(debug_info.files) == 1

    outfile.write(debug_info.files[0].contents)
    outfile.write(f"\n\n\n")


def _dump_outputs(action, pipeline, output_path):
    fb = pipeline.framebuffer
    if not fb:
        return
    draw_fbo = fb.drawFBO
    if not draw_fbo:
        return

    def save(resource_id, filename, alpha=renderdoc.AlphaMapping.Preserve):
        texsave = renderdoc.TextureSave()
        texsave.resourceId = resource_id
        filename = os.path.join(output_path, filename)
        texsave.mip = 0
        texsave.slice.sliceIndex = 0
        texsave.alpha = renderdoc.AlphaMapping.Preserve
        texsave.destType = renderdoc.FileType.PNG

        replay_manager.BlockInvoke(
            lambda controller: controller.SaveTexture(texsave, filename + ".png")
        )

    dumped = set()
    for index, resource in enumerate(draw_fbo.colorAttachments):
        resource_id = resource.resourceId
        if resource_id == renderdoc.ResourceId.Null():
            continue
        if resource_id in dumped:
            continue
        dumped.add(resource_id)
        save(resource_id, f"EID_{action.eventId}_color_{index}-{resource_id}-a")
        save(
            resource_id,
            f"EID_{action.eventId}_color_{index}-{resource_id}",
            renderdoc.AlphaMapping.Discard,
        )

    depth = draw_fbo.depthAttachment
    if depth:
        resource_id = depth.resourceId
        if resource_id != renderdoc.ResourceId.Null() and resource_id not in dumped:
            save(resource_id, f"EID_{action.eventId}_depth-{resource_id}")

    psh = pipeline.fragmentShader
    bindpoint_mapping = psh.bindpointMapping

    resources = psh.reflection.readOnlyResources
    ro_inputs = bindpoint_mapping.readOnlyResources
    rw_inputs = bindpoint_mapping.readWriteResources

    for resource in resources:
        if not resource.isTexture:
            continue

        bindpoint_array = ro_inputs if resource.isReadOnly else rw_inputs
        bindpoint = bindpoint_array[resource.bindPoint]
        if not bindpoint.used:
            continue
        texture = pipeline.textures[resource.bindPoint]
        resource_id = texture.resourceId
        save(resource_id, f"EID_{action.eventId}_tex{resource.bindPoint}-{resource_id}")


def iterate_draw_actions(action):
    while action:
        if action.flags & renderdoc.ActionFlags.Drawcall:
            yield action
        action = action.next


def dump_draws():
    vsh_processed = set()
    psh_processed = set()

    current_filename = os.path.basename(context.GetCaptureFilename())
    output_path = os.path.expanduser(f"~/Desktop/{current_filename}_dump")
    os.makedirs(output_path, exist_ok=True)

    with open(os.path.join(output_path, "shaders.glsl"), "w") as outfile:
        for action in iterate_draw_actions(context.CurRootActions()[0]):
            if not action.flags & renderdoc.ActionFlags.Drawcall:
                action = action.next
                continue
            context.SetEventID([], action.eventId, action.eventId, False)
            pipeline = context.CurGLPipelineState()
            if not pipeline:
                action = action.next
                continue

            outfile.write(f"// EID: {action.eventId}\n")
            vsh = pipeline.vertexShader
            vsh_id = vsh.programResourceId
            outfile.write(f"// Vertex shader: {vsh_id}\n")
            if vsh_id not in vsh_processed:
                vsh_processed.add(vsh_id)
                dump_shader_contents(vsh, outfile)

            psh = pipeline.fragmentShader
            psh_id = psh.programResourceId
            outfile.write(f"// Pixel shader: {psh_id}\n")
            if psh_id not in psh_processed:
                psh_processed.add(vsh_id)
                dump_shader_contents(psh, outfile)

            _dump_outputs(action, pipeline, output_path)

            action = action.next


dump_draws()
