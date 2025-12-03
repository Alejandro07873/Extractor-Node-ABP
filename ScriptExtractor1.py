import json
import pyperclip
import sys


def format_float(val):
    return f"{val:.6f}"


def format_vector3(v):
    if v is None:
        return "(X=0.000000,Y=0.000000,Z=0.000000)"
    return f"(X={format_float(v.get('X', 0))},Y={format_float(v.get('Y', 0))},Z={format_float(v.get('Z', 0))})"


def bool_lower(b):
    if b is None:
        return None
    return str(b).lower()


def enum_last(e):
    if e is None:
        return None
    return e.split("::")[-1]


def format_limits(limits, t):
    if not limits:
        return None
    formatted = []
    for lm in limits:
        r = format_float(lm.get("Radius", 0))
        l = format_float(lm.get("Length", 1))
        bone = lm.get("DrivingBone", {}).get("BoneName", "None")
        ol = lm.get("OffsetLocation", {})
        orot = lm.get("OffsetRotation", {})

        formatted.append(
            f"(Radius={r},Length={l},DrivingBone=(BoneName=\"{bone}\"),"
            f"OffsetLocation=(X={format_float(ol.get('X', 0))},Y={format_float(ol.get('Y', 0))},Z={format_float(ol.get('Z', 0))}),"
            f"OffsetRotation=(Pitch={format_float(orot.get('Pitch', 0))},Yaw={format_float(orot.get('Yaw', 0))},Roll={format_float(orot.get('Roll', 0))}))"
        )
    return f"{t}=({','.join(formatted)})"


def format_component_pose(node):
    cp = node.get("ComponentPose")
    if cp and cp.get("LinkID") is not None:
        return f",ComponentPose=(LinkID={cp['LinkID']})"
    return ""


def format_base_anim_fields(node):
    parts = []

    if node.get("LODThreshold") is not None:
        parts.append(f"LODThreshold={int(node['LODThreshold'])}")

    if node.get("ActualAlpha") is not None:
        parts.append(f"ActualAlpha={format_float(node['ActualAlpha'])}")

    if node.get("AlphaInputType"):
        parts.append(f"AlphaInputType={enum_last(node['AlphaInputType'])}")

    if node.get("bAlphaBoolEnabled") is not None:
        parts.append(f"bAlphaBoolEnabled={bool_lower(node['bAlphaBoolEnabled'])}")

    if node.get("AlphaCurveName"):
        parts.append(f"AlphaCurveName=\"{node['AlphaCurveName']}\"")

    c = node.get("AlphaScaleBiasClamp")
    if c:
        parts.append(
            "AlphaScaleBiasClamp=("
            f"bMapRange={bool_lower(c.get('bMapRange'))},"
            f"bClampResult={bool_lower(c.get('bClampResult'))},"
            f"bInterpResult={bool_lower(c.get('bInterpResult'))},"
            f"InRange=(Min={format_float(c['InRange']['Min'])},Max={format_float(c['InRange']['Max'])}),"
            f"OutRange=(Min={format_float(c['OutRange']['Min'])},Max={format_float(c['OutRange']['Max'])}),"
            f"Scale={format_float(c['Scale'])},Bias={format_float(c['Bias'])},"
            f"ClampMin={format_float(c['ClampMin'])},ClampMax={format_float(c['ClampMax'])},"
            f"InterpSpeedIncreasing={format_float(c['InterpSpeedIncreasing'])},"
            f"InterpSpeedDecreasing={format_float(c['InterpSpeedDecreasing'])}"
            ")"
        )

    if parts:
        return "," + ",".join(parts)
    return ""


def run_extractor(InputJsonPath, OutputTxtPath, AnimBPClass):
    """
    Procesa el JSON de FModel y genera el TXT con los nodos Kawaii/AnimGraph.
    También copia el resultado al portapapeles.
    """

    
    with open(InputJsonPath, "r", encoding="utf-8") as f:
        jsonContent = json.load(f)

    target = None
    for entry in jsonContent:
        if entry.get("Type") == AnimBPClass:
            target = entry
            break

    if target is None:
        raise ValueError(f"Could not find {AnimBPClass} object in JSON.")

    props = target["Properties"]
    output = []
    index = 0

  
    for key, node in props.items():


        if key.startswith("AnimGraphNode_KawaiiPhysics"):
            rootBone = node["RootBone"]["BoneName"]
            dummy = format_float(node["DummyBoneLength"])
            axis = enum_last(node["BoneForwardAxis"])
            tpdist = format_float(node["TeleportDistanceThreshold"])
            tprot = format_float(node["TeleportRotationThreshold"])

            ps = node.get("PhysicsSettings")
            if ps:
                physicsStr = (
                    f"Damping={format_float(ps['Damping'])},"
                    f"Stiffness={format_float(ps['Stiffness'])},"
                    f"WorldDampingLocation={format_float(ps['WorldDampingLocation'])},"
                    f"WorldDampingRotation={format_float(ps['WorldDampingRotation'])},"
                    f"Radius={format_float(ps['Radius'])},"
                    f"LimitAngle={format_float(ps['LimitAngle'])}"
                )
            else:
                physicsStr = ""

            extra = ""
            for limType, limName in [
                (node.get("CapsuleLimits"), "CapsuleLimits"),
                (node.get("SphericalLimits"), "SphericalLimits"),
                (node.get("PlanarLimits"), "PlanarLimits"),
            ]:
                f_lim = format_limits(limType, limName)
                if f_lim:
                    extra += "," + f_lim

            curve = node.get("LimitAngleCurve")
            if curve and curve.get("ObjectName"):
                extra += f",LimitAngleCurve=(ObjectName=\"{curve['ObjectName']}\",ObjectPath=\"{curve['ObjectPath']}\")"

            if node.get("bEnableWind") is not None:
                extra += f",bEnableWind={bool_lower(node['bEnableWind'])}"

            if node.get("WindScale") is not None:
                extra += f",WindScale={format_float(node['WindScale'])}"

            if node.get("Gravity"):
                extra += f",Gravity={format_vector3(node['Gravity'])}"

            if node.get("AlphaScaleBias"):
                asb = node["AlphaScaleBias"]
                extra += f",AlphaScaleBias=(Scale={format_float(asb['Scale'])},Bias={format_float(asb['Bias'])})"

            if node.get("AlphaBoolBlend"):
                bb = node["AlphaBoolBlend"]
                extra += (
                    f",AlphaBoolBlend=(BlendInTime={format_float(bb['BlendInTime'])},"
                    f"BlendOutTime={format_float(bb['BlendOutTime'])},BlendOption={bb['BlendOption']})"
                )

            base = format_base_anim_fields(node)
            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics Name="{key}"
   Node=(RootBone=(BoneName="{rootBone}"),DummyBoneLength={dummy},BoneForwardAxis={axis},TeleportDistanceThreshold={tpdist},TeleportRotationThreshold={tprot},PhysicsSettings=({physicsStr}){extra}{base}{cp})
   ShowPinForProperties(0)=(PropertyName="ComponentPose",bShowPin=True)
   ShowPinForProperties(1)=(PropertyName="bAlphaBoolEnabled",bShowPin=True)
   ShowPinForProperties(2)=(PropertyName="Alpha",bShowPin=True)
   ShowPinForProperties(3)=(PropertyName="AlphaCurveName",bShowPin=True)
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

        
        elif key.startswith("AnimGraphNode_ModifyBone"):
            bone = node["BoneToModify"]["BoneName"]
            t = node["Translation"]
            r = node["Rotation"]
            s = node["Scale"]

            tmode = enum_last(node["TranslationMode"])
            rmode = enum_last(node["RotationMode"])
            smode = enum_last(node["ScaleMode"])
            tspace = enum_last(node["TranslationSpace"])
            rspace = enum_last(node["RotationSpace"])
            sspace = enum_last(node["ScaleSpace"])

            base = format_base_anim_fields(node)
            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/AnimGraph.AnimGraphNode_ModifyBone Name="{key}"
   Node=(BoneToModify=(BoneName="{bone}"),Translation=(X={format_float(t['X'])},Y={format_float(t['Y'])},Z={format_float(t['Z'])}),Rotation=(Pitch={format_float(r['Pitch'])},Yaw={format_float(r['Yaw'])},Roll={format_float(r['Roll'])}),Scale=(X={format_float(s['X'])},Y={format_float(s['Y'])},Z={format_float(s['Z'])}),TranslationMode={tmode},RotationMode={rmode},ScaleMode={smode},TranslationSpace={tspace},RotationSpace={rspace},ScaleSpace={sspace}{base}{cp})
   ShowPinForProperties(0)=(PropertyName="ComponentPose",bShowPin=True)
   ShowPinForProperties(1)=(PropertyName="bAlphaBoolEnabled",bShowPin=True)
   ShowPinForProperties(2)=(PropertyName="Alpha",bShowPin=True)
   ShowPinForProperties(3)=(PropertyName="AlphaCurveName",bShowPin=True)
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

       
        elif key.startswith("AnimGraphNode_CopyBone"):
            src = node["SourceBone"]["BoneName"]
            tgt = node["TargetBone"]["BoneName"]

            bT = bool_lower(node["bCopyTranslation"])
            bR = bool_lower(node["bCopyRotation"])
            bS = bool_lower(node["bCopyScale"])

            alpha = format_float(node.get("Alpha", 1.0))
            space = enum_last(node["ControlSpace"])

            alphaSB = ""
            if node.get("AlphaScaleBias"):
                asb = node["AlphaScaleBias"]
                alphaSB = f",AlphaScaleBias=(Scale={format_float(asb['Scale'])},Bias={format_float(asb['Bias'])})"

            alphaBB = ""
            if node.get("AlphaBoolBlend"):
                bb = node["AlphaBoolBlend"]
                alphaBB = (
                    f",AlphaBoolBlend=(BlendInTime={format_float(bb['BlendInTime'])},"
                    f"BlendOutTime={format_float(bb['BlendOutTime'])},BlendOption={bb['BlendOption']})"
                )

            base = format_base_anim_fields(node)
            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/AnimGraph.AnimGraphNode_CopyBone Name="{key}"
   Node=(SourceBone=(BoneName="{src}"),TargetBone=(BoneName="{tgt}"),bCopyTranslation={bT},bCopyRotation={bR},bCopyScale={bS},ControlSpace={space},Alpha={alpha}{alphaSB}{alphaBB}{base}{cp})
   ShowPinForProperties(0)=(PropertyName="ComponentPose",bShowPin=True)
   ShowPinForProperties(1)=(PropertyName="bAlphaBoolEnabled",bShowPin=True)
   ShowPinForProperties(2)=(PropertyName="Alpha",bShowPin=True)
   ShowPinForProperties(3)=(PropertyName="AlphaCurveName",bShowPin=True)
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

       
        elif key.startswith("AnimGraphNode_Constraint"):
            bone = node["BoneToModify"]["BoneName"]

            setupEntries = []
            for cs in node.get("ConstraintSetup", []):
                if cs:
                    tb = cs["TargetBone"]["BoneName"]
                    off = enum_last(cs["OffsetOption"])
                    tt = enum_last(cs["TransformType"])
                    px = bool_lower(cs["PerAxis"]["bX"])
                    py = bool_lower(cs["PerAxis"]["bY"])
                    pz = bool_lower(cs["PerAxis"]["bZ"])

                    setupEntries.append(
                        f"(TargetBone=(BoneName=\"{tb}\"),OffsetOption={off},TransformType={tt},PerAxis=(bX={px},bY={py},bZ={pz}))"
                    )

            weights = []
            if node.get("ConstraintWeights"):
                weights = [format_float(w) for w in node["ConstraintWeights"]]

            setupStr = ",".join(setupEntries)
            weightsStr = ",".join(weights)

            base = format_base_anim_fields(node)
            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/AnimGraph.AnimGraphNode_Constraint Name="{key}"
   Node=(BoneToModify=(BoneName="{bone}"),ConstraintSetup=({setupStr}),ConstraintWeights=({weightsStr}){base}{cp})
   ShowPinForProperties(0)=(PropertyName="ComponentPose",bShowPin=True)
   ShowPinForProperties(1)=(PropertyName="bAlphaBoolEnabled",bShowPin=True)
   ShowPinForProperties(2)=(PropertyName="Alpha",bShowPin=True)
   ShowPinForProperties(3)=(PropertyName="AlphaCurveName",bShowPin=True)
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

      
        elif key.startswith("AnimGraphNode_RotationMultiplier"):
            tgt = node["TargetBone"]["BoneName"]
            src = node["SourceBone"]["BoneName"]
            mul = format_float(node.get("Multiplier", 1.0))
            axis = enum_last(node["RotationAxisToRefer"])

            base = format_base_anim_fields(node)
            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/AnimGraph.AnimGraphNode_RotationMultiplier Name="{key}"
   Node=(TargetBone=(BoneName="{tgt}"),SourceBone=(BoneName="{src}"),Multiplier={mul},RotationAxisToRefer={axis}{base}{cp})
   ShowPinForProperties(0)=(PropertyName="ComponentPose",bShowPin=True)
   ShowPinForProperties(1)=(PropertyName="bAlphaBoolEnabled",bShowPin=True)
   ShowPinForProperties(2)=(PropertyName="Alpha",bShowPin=True)
   ShowPinForProperties(3)=(PropertyName="AlphaCurveName",bShowPin=True)
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

       
        elif key.startswith("AnimGraphNode_LayeredBoneBlend"):
            layers = []
            for layer in node.get("LayerSetup", []):
                if layer:
                    filters = [
                        f'(BoneName="{f["BoneName"]}",BlendDepth={int(f.get("BlendDepth", 0))})'
                        for f in layer.get("BranchFilters", [])
                        if f
                    ]
                    layers.append(f"(BranchFilters=({','.join(filters)}))")

            layerSetup = f"LayerSetup=({','.join(layers)})"

            meshRot = bool_lower(node.get("bMeshSpaceRotationBlend"))
            meshScale = bool_lower(node.get("bMeshSpaceScaleBlend"))
            curveBlend = enum_last(node.get("CurveBlendOption"))
            blendRoot = bool_lower(node.get("bBlendRootMotionBasedOnRootBone"))

            weightsPart = ""
            if node.get("BlendWeights"):
                w = [format_float(x) for x in node["BlendWeights"]]
                weightsPart = f",BlendWeights=({','.join(w)})"

            base = format_base_anim_fields(node)
            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/AnimGraph.AnimGraphNode_LayeredBoneBlend Name="{key}"
   Node=({layerSetup},bMeshSpaceRotationBlend={meshRot},bMeshSpaceScaleBlend={meshScale},CurveBlendOption={curveBlend},bBlendRootMotionBasedOnRootBone={blendRoot}{weightsPart}{base}{cp})
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

       
        elif key.startswith("AnimGraphNode_RigidBody"):
            extra = ""

            if node.get("OverrideWorldGravity") is not None:
                extra += f",OverrideWorldGravity={bool_lower(node['OverrideWorldGravity'])}"

            if node.get("WorldSpaceGravityScale") is not None:
                extra += f",WorldSpaceGravityScale={format_float(node['WorldSpaceGravityScale'])}"

            if node.get("ComponentLinearAccScale") is not None:
                extra += f",ComponentLinearAccScale={format_float(node['ComponentLinearAccScale'])}"

            if node.get("CachedBoundsScale") is not None:
                extra += f",CachedBoundsScale={format_float(node['CachedBoundsScale'])}"

            if node.get("BaseBoneRef"):
                extra += f",BaseBoneRef=(BoneName=\"{node['BaseBoneRef']['BoneName']}\")"

            base = format_base_anim_fields(node)
            extra += base
            extra = extra.lstrip(",")

            cp = format_component_pose(node)

            posX = 0
            posY = index * 144

            output.append(f"""
Begin Object Class=/Script/AnimGraph.AnimGraphNode_RigidBody Name="{key}"
   Node=({extra}{cp})
   ShowPinForProperties(0)=(PropertyName="ComponentPose",bShowPin=True)
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

        
        elif key.startswith("AnimGraphNode_"):
            base = format_base_anim_fields(node)
            cp = format_component_pose(node)
            posX = 0
            posY = index * 144
            classPath = f"/Script/AnimGraph.{key}"

            output.append(f"""
Begin Object Class={classPath} Name="{key}"
   Node=({base}{cp})
   NodePosX={posX}
   NodePosY={posY}
End Object
""")
            index += 1

   
    final_output = "\n".join(output)

    with open(OutputTxtPath, "w", encoding="utf-8") as f:
        f.write(final_output)

    pyperclip.copy(final_output)



if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: ScriptExtractor.py <input.json> <output.txt> <AnimBPClass>")
        sys.exit(1)

    run_extractor(sys.argv[1], sys.argv[2], sys.argv[3])
    print("Export complete. Copied to clipboard.")
