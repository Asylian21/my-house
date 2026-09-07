import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import type { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { buildInterior } from "../lib/babylon-interior";
import type { AnimatedDoorRegistration } from "../lib/babylon-doors";
import {
  BATHROOM_FITOUT,
  CHILDRENS_BEDROOM_FITOUTS,
  FIREPLACE_STOVE,
  GARAGE_FITOUT,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_WALLS,
  OFFICE_FITOUT,
  TECHNICAL_HEATING_FITOUT,
  WC_FITOUT,
} from "../lib/twin-interior";
import { MM_TO_M, sceneXM, sceneZM } from "../lib/twin-render-frame";

describe("Babylon interior fit-out", () => {
  it("builds the required room objects and measured collision envelopes", () => {
    const engine = new NullEngine({
      renderHeight: 256,
      renderWidth: 256,
      textureSize: 256,
    });
    const scene = new Scene(engine);
    const material = (name: string) => new PBRMaterial(name, scene);
    const doors: AnimatedDoorRegistration[] = [];
    try {
      buildInterior({
        scene,
        anisotropy: 1,
        wall: material("test-wall"),
        soffit: material("test-soffit"),
        glassFrame: material("test-glass-frame"),
        chimneyMetal: material("test-chimney-metal"),
        timber: material("test-timber"),
        register: (mesh: AbstractMesh) => mesh,
        realisticOnly: (mesh: AbstractMesh) => mesh,
        castShadow: (mesh: AbstractMesh) => mesh,
        registerAnimatedDoor: (door) => doors.push(door),
      });

      const architecturalDoors = doors.filter((door) =>
        INTERIOR_DOORS.some(({ id }) => id === door.id),
      );
      const applianceDoors = doors.filter((door) =>
        BATHROOM_FITOUT.builtIn.appliances.some(
          (appliance) => appliance.door.id === door.id,
        ),
      );
      expect(architecturalDoors.map(({ id }) => id).sort()).toEqual(
        INTERIOR_DOORS.map(({ id }) => id).sort(),
      );
      expect(architecturalDoors).toHaveLength(10);
      expect(applianceDoors.map(({ id }) => id).sort()).toEqual(
        BATHROOM_FITOUT.builtIn.appliances.map(({ door }) => door.id).sort(),
      );
      expect(doors).toHaveLength(12);

      const walkSurfaces = scene.meshes.filter(
        (mesh) => mesh.metadata?.walkSurface === true,
      );
      expect(walkSurfaces.length).toBeGreaterThan(INTERIOR_DOORS.length);
      expect(
        walkSurfaces.every(
          (mesh) =>
            mesh.metadata?.walkSurfaceKind === "interior" &&
            typeof mesh.metadata?.walkSurfaceId === "string",
        ),
      ).toBe(true);
      for (const overheadMarker of [
        "· horné skrinky",
        "· horná skrinka nad zrkadlom",
        "· LAUNDRY-TOWER · vetraná horná skrinka",
        "· OVERHEAD · horná úložná skriňa",
        "· CABINET · horný blok",
        "LIVING-103-TV-WALL · horný úložný most",
      ]) {
        const overhead = scene.meshes.find((mesh) =>
          mesh.name.includes(overheadMarker),
        );
        expect(overhead, `${overheadMarker} protects the chase camera`).toBeDefined();
        expect(overhead?.metadata?.cameraOccluder).toBe(true);
      }

      for (const door of architecturalDoors) {
        const leaf = scene.meshes.find(
          (mesh) =>
            mesh.metadata?.doorId === door.id &&
            mesh.name.includes("animované krídlo"),
        );
        expect(leaf, `${door.id} has one moving leaf`).toBeDefined();
        expect(leaf?.checkCollisions).toBe(true);
        expect(leaf?.isPickable).toBe(true);
        expect(leaf?.metadata).toMatchObject({
          doorId: door.id,
          doorMotion: door.kind,
          dynamicCameraOccluder: true,
        });
        const handles = scene.meshes.filter(
          (mesh) =>
            mesh.parent === leaf?.parent && mesh.name.includes("kľučka"),
        );
        expect(handles, `${door.id} has a handle on both faces`).toHaveLength(2);
        door.apply(1, 1);
        const movingRoot = leaf?.parent as TransformNode | null;
        if (door.kind === "SLIDING") {
          expect(Math.hypot(
            movingRoot?.position.x ?? 0,
            movingRoot?.position.z ?? 0,
          )).toBeCloseTo(INTERIOR_DOORS.find(spec=>spec.id===door.id)!.pocketTravelMm! / 1000, 8);
          expect(movingRoot?.rotation.y ?? 0).toBe(0);
        } else {
          expect(Math.abs(movingRoot?.rotation.y ?? 0)).toBeCloseTo(
            Math.PI / 2,
            8,
          );
        }
        expect(
          door.canOpen?.({
            position: door.interactionPoint,
            facing: { x: 1, z: 0 },
          }),
        ).toBe(false);
        expect(
          door.canClose?.({
            position: {
              x: door.interactionPoint.x + 5,
              z: door.interactionPoint.z + 5,
            },
            facing: { x: 1, z: 0 },
          }),
        ).toBe(true);
        door.apply(0, 0);
      }

      const wcDoor = architecturalDoors.find((door) => door.id === "DOOR-102-106")!;
      const wcLeaf = scene.meshes.find(
        (mesh) =>
          mesh.metadata?.doorId === wcDoor.id
          && mesh.name.includes("animované krídlo"),
      )!;
      const wcEdgePull = scene.meshes.find(
        (mesh) =>
          mesh.metadata?.doorId === wcDoor.id
          && mesh.name.includes("čelné výsuvné madlo"),
      )!;
      wcDoor.apply(1, 0);
      const wcMovingRoot = wcLeaf.parent as TransformNode;
      expect(wcDoor.kind).toBe("SLIDING");
      expect(wcEdgePull.isPickable).toBe(true);
      expect(wcMovingRoot.position.x).toBeCloseTo(0, 8);
      expect(wcMovingRoot.position.z).toBeCloseTo(0.76, 8);
      wcEdgePull.computeWorldMatrix(true);
      const wcDoorSpec = INTERIOR_DOORS.find((door) => door.id === wcDoor.id)!;
      expect(wcEdgePull.getAbsolutePosition().z).toBeCloseTo(sceneZM(9870), 6);
      expect(
        Math.abs(
          wcEdgePull.getAbsolutePosition().z - sceneZM(wcDoorSpec.startMm),
        ),
      ).toBeLessThanOrEqual(0.02);
      const wcRoom = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-06")!;
      const wcActor = {
        position: {
          x: sceneXM(wcRoom.standingPointMm.x),
          z: sceneZM(wcRoom.standingPointMm.y),
        },
        facing: { x: -1, z: 0 },
        radiusM: 0.22,
      };
      expect(wcDoor.canOpen?.(wcActor, 0)).toBe(true);
      expect(wcDoor.canClose?.(wcActor, 1)).toBe(true);
      wcDoor.apply(0, 0);

      const applianceHinges = new Map(
        BATHROOM_FITOUT.builtIn.appliances.map((appliance) => [
          appliance.door.id,
          scene.transformNodes.find(
            (node) => node.metadata?.doorId === appliance.door.id,
          ) as TransformNode | undefined,
        ]),
      );
      for (const appliance of BATHROOM_FITOUT.builtIn.appliances) {
        const registration = applianceDoors.find(
          (door) => door.id === appliance.door.id,
        )!;
        const hinge = applianceHinges.get(appliance.door.id);
        expect(registration).toMatchObject({
          id: appliance.door.id,
          label: appliance.kind === "WASHER" ? "Práčka" : "Sušička",
          kind: "HINGED",
          subject: "APPLIANCE_DOOR",
        });
        expect(registration.interactionPoint.y).toBeCloseTo(
          appliance.door.centerElevationMm * MM_TO_M,
          8,
        );
        expect(hinge, `${appliance.kind} has a real pivot`).toBeDefined();
        expect(hinge?.rotation.y).toBe(0);
        const movingMeshes = scene.meshes.filter(
          (mesh) =>
            mesh.parent === hinge && mesh.metadata?.doorId === appliance.door.id,
        );
        expect(movingMeshes).toHaveLength(3);
        expect(movingMeshes.every((mesh) => mesh.isPickable)).toBe(true);
        expect(
          movingMeshes.every(
            (mesh) => mesh.metadata?.dynamicCameraOccluder === true,
          ),
        ).toBe(true);
        expect(
          movingMeshes.find((mesh) => mesh.name.includes("· rám"))
            ?.checkCollisions,
        ).toBe(true);
        registration.apply(1, 0);
        expect(hinge?.rotation.y).toBeCloseTo(-Math.PI / 2, 8);
        registration.apply(0, 0);
      }
      const [washerHinge, dryerHinge] = BATHROOM_FITOUT.builtIn.appliances.map(
        (appliance) => applianceHinges.get(appliance.door.id)!,
      );
      applianceDoors.find(({ id }) => id === "BATH-105-WASHER-DOOR")!.apply(1, 0);
      expect(washerHinge.rotation.y).toBeCloseTo(-Math.PI / 2, 8);
      expect(dryerHinge.rotation.y).toBeCloseTo(0, 12);
      applianceDoors.find(({ id }) => id === "BATH-105-WASHER-DOOR")!.apply(0, 0);

      for (const fitout of CHILDRENS_BEDROOM_FITOUTS) {
        const roomMeshes = scene.meshes.filter((mesh) => mesh.name.startsWith(fitout.id));
        for (const required of ["· BED ·", "· WARDROBE ·", "· DESK ·", "· CHAIR ·"]) {
          expect(
            roomMeshes.some((mesh) => mesh.name.includes(required)),
            `${fitout.id} renders ${required}`,
          ).toBe(true);
        }

        const mattress=roomMeshes.find(mesh=>mesh.name.includes('· BED · matrac'))!;
        mattress.computeWorldMatrix(true);
        const bounds=mattress.getBoundingInfo().boundingBox;
        expect(bounds.maximumWorld.x-bounds.minimumWorld.x).toBeCloseTo(1.4,3);
        expect(bounds.maximumWorld.z-bounds.minimumWorld.z).toBeCloseTo(2,3);
        expect(bounds.maximumWorld.y).toBeCloseTo(.46,3);
        const positions=mattress.getVerticesData('position')!;
        const normals=mattress.getVerticesData('normal')!;
        const indices=mattress.getIndices()!;
        for(let i=0;i<indices.length;i+=3){
          const [a,b,c]=[indices[i]*3,indices[i+1]*3,indices[i+2]*3];
          const ab=[0,1,2].map(axis=>positions[b+axis]-positions[a+axis]);
          const ac=[0,1,2].map(axis=>positions[c+axis]-positions[a+axis]);
          const cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];
          expect(cross.reduce((sum,value,axis)=>sum+value*normals[a+axis],0),'upholstery front face follows Babylon winding').toBeLessThan(0);
        }
        expect(roomMeshes.filter(mesh=>mesh.name.includes('čalúnené čelo'))).toHaveLength(2);
        const duvet=roomMeshes.find(mesh=>mesh.name.includes('mäkko skladaná ľanová prikrývka'))!;
        const duvetNormals=duvet.getVerticesData('normal')!;
        const duvetPositions=duvet.getVerticesData('position')!;
        const layerVertices=duvetPositions.length/6;
        const centerVertex=Math.floor(layerVertices/2);
        expect(duvetPositions[centerVertex*3+1]).toBeGreaterThan(duvetPositions[(centerVertex+layerVertices)*3+1]);
        expect(duvetNormals[centerVertex*3+1]).toBeGreaterThan(.9);
        expect(duvetNormals[(centerVertex+layerVertices)*3+1]).toBeLessThan(-.9);

        const guards = roomMeshes.filter((mesh) => mesh.metadata?.walkCollisionOnly === true);
        expect(guards.map((guard) => guard.name)).toEqual(expect.arrayContaining([
          expect.stringContaining("· BED · navigačný obrys"),
          expect.stringContaining("· WARDROBE · navigačný obrys"),
          expect.stringContaining("· DESK · navigačný obrys"),
          expect.stringContaining("· CHAIR · navigačný obrys"),
          expect.stringContaining("· TOYS · navigačný obrys"),
          expect.stringContaining("· BOOKS · navigačný obrys"),
          expect.stringContaining("· READING · navigačný obrys"),
        ]));
        expect(guards).toHaveLength(7);
        for (const guard of guards) {
          expect(guard.checkCollisions).toBe(true);
          expect(guard.isVisible).toBe(false);
        }
      }

      const officeMeshes = scene.meshes.filter((mesh) =>
        mesh.name.startsWith(OFFICE_FITOUT.id),
      );
      for (const required of [
        "· CABINET ·",
        "· PRINTER ·",
        "· DESK ·",
        "· MONITOR-40-21:9 ·",
        "· CHAIR ·",
        "· WHITEBOARD ·",
      ]) {
        expect(
          officeMeshes.some((mesh) => mesh.name.includes(required)),
          `office renders ${required}`,
        ).toBe(true);
      }

      const officeGuards = officeMeshes.filter(
        (mesh) => mesh.metadata?.walkCollisionOnly === true,
      );
      expect(officeGuards).toHaveLength(3);
      const expectedOfficeGuards = [
        ["· CABINET · navigačný obrys", OFFICE_FITOUT.cabinet.footprintMm],
        ["· DESK · navigačný obrys", OFFICE_FITOUT.desk.footprintMm],
        ["· CHAIR · navigačný obrys pojazdu", OFFICE_FITOUT.chair.footprintMm],
      ] as const;
      for (const [marker, footprint] of expectedOfficeGuards) {
        const guard = officeGuards.find((mesh) => mesh.name.includes(marker));
        expect(guard, `${marker} exists`).toBeDefined();
        expect(guard?.checkCollisions).toBe(true);
        expect(guard?.isVisible).toBe(false);
        guard?.computeWorldMatrix(true);
        const bounds = guard?.getBoundingInfo().boundingBox;
        expect((bounds?.extendSizeWorld.x ?? 0) * 2).toBeCloseTo(
          (footprint.x1 - footprint.x0) * MM_TO_M,
          8,
        );
        expect((bounds?.extendSizeWorld.z ?? 0) * 2).toBeCloseTo(
          (footprint.y1 - footprint.y0) * MM_TO_M,
          8,
        );
        expect(guard?.position.x).toBeCloseTo(
          sceneXM((footprint.x0 + footprint.x1) / 2),
          8,
        );
        expect(guard?.position.z).toBeCloseTo(
          sceneZM((footprint.y0 + footprint.y1) / 2),
          8,
        );
      }

      const cabinetNicheBack = officeMeshes.find((mesh) =>
        mesh.name.includes("· CABINET · tmavý chrbát tlačiarňového výklenku"),
      );
      const cabinetFrontSeams = officeMeshes.filter((mesh) =>
        mesh.name.includes("· CABINET · zvislá tieňová škára"),
      );
      expect(cabinetNicheBack?.position.x).toBeCloseTo(
        sceneXM(OFFICE_FITOUT.cabinet.printerNiche.footprintMm.x1 - 8),
        8,
      );
      expect(cabinetFrontSeams).toHaveLength(2);
      expect(
        cabinetFrontSeams.every(
          (mesh) => mesh.position.x < sceneXM(OFFICE_FITOUT.cabinet.footprintMm.x0),
        ),
      ).toBe(true);

      const printerBody = officeMeshes.find((mesh) =>
        mesh.name.includes("· PRINTER · biele telo integrovanej tlačiarne"),
      );
      for (const frontDetail of [
        "· PRINTER · čierny výstup papiera",
        "· PRINTER · dotykový ovládací panel",
        "· PRINTER · čistý papier vo výstupe",
      ]) {
        const mesh = officeMeshes.find((candidate) =>
          candidate.name.includes(frontDetail),
        );
        expect(mesh, `${frontDetail} exists`).toBeDefined();
        expect(mesh?.position.x).toBeLessThan(printerBody?.position.x ?? 0);
      }

      const monitorShells = officeMeshes.filter((mesh) =>
        mesh.name.includes("· MONITOR-40-21:9 · zakrivený zadný segment"),
      );
      const monitorGlass = officeMeshes.filter((mesh) =>
        mesh.name.includes("· MONITOR-40-21:9 · obrazový segment"),
      );
      expect(monitorShells).toHaveLength(9);
      expect(monitorGlass).toHaveLength(9);
      for (let index = 0; index < 9; index += 1) {
        expect(monitorGlass[index].position.x).toBeGreaterThan(
          monitorShells[index].position.x,
        );
      }
      const monitorPlanSpanM =
        Math.max(...monitorShells.map((mesh) => mesh.position.z)) -
        Math.min(...monitorShells.map((mesh) => mesh.position.z));
      expect(monitorPlanSpanM).toBeGreaterThan(0.8);
      expect(
        monitorShells.every(
          (mesh) => mesh.position.x >= sceneXM(OFFICE_FITOUT.desk.monitor.centerMm.x),
        ),
      ).toBe(true);

      const chairBack = officeMeshes.find((mesh) =>
        mesh.name.includes("· CHAIR · vysoké ergonomické operadlo"),
      );
      const chairArmPosts = officeMeshes.filter((mesh) =>
        mesh.name.includes("· CHAIR · nastaviteľná podrúčka"),
      );
      expect(chairBack?.position.x).toBeGreaterThan(
        sceneXM(OFFICE_FITOUT.chair.centerMm.x),
      );
      expect(chairArmPosts).toHaveLength(2);
      expect(
        chairArmPosts.every(
          (mesh) => mesh.position.x < sceneXM(OFFICE_FITOUT.chair.centerMm.x),
        ),
      ).toBe(true);

      const officeCableTray = officeMeshes.find((mesh) =>
        mesh.name.includes("· DESK · skrytý káblový žľab"),
      );
      const officeLight = officeMeshes.find((mesh) =>
        mesh.name.includes("· LIGHT · čierny lineárny stropný profil"),
      );
      for (const [mesh, widthM, depthM] of [
        [officeCableTray, 0.15, 0.88],
        [officeLight, 0.058, 1.26],
      ] as const) {
        mesh?.computeWorldMatrix(true);
        const bounds = mesh?.getBoundingInfo().boundingBox;
        expect((bounds?.extendSizeWorld.x ?? 0) * 2).toBeCloseTo(widthM, 8);
        expect((bounds?.extendSizeWorld.z ?? 0) * 2).toBeCloseTo(depthM, 8);
      }

      const heatingMeshes = scene.meshes.filter((mesh) =>
        mesh.name.startsWith(TECHNICAL_HEATING_FITOUT.id),
      );
      for (const required of [
        "· WOOD-PELLET-BOILER ·",
        "· PELLET-HOPPER ·",
        "· PELLET-AUGER ·",
        "· PELLET-FEED-HOSE ·",
        "· PELLET-BURNER ·",
        "· BUFFER-TANK-1000L ·",
      ]) {
        expect(
          heatingMeshes.some((mesh) => mesh.name.includes(required)),
          `technical heating renders ${required}`,
        ).toBe(true);
      }

      const hose = heatingMeshes.find((mesh) => mesh.name.includes("· PELLET-FEED-HOSE ·"));
      expect(hose?.getTotalVertices()).toBeGreaterThan(0);
      expect(
        heatingMeshes.find((mesh) => mesh.name.includes("kombinované teleso"))?.isPickable,
      ).toBe(true);
      expect(
        heatingMeshes.find((mesh) => mesh.name.includes("zásobník peliet približne"))
          ?.isPickable,
      ).toBe(true);

      const heatingGuards = heatingMeshes.filter(
        (mesh) => mesh.metadata?.walkCollisionOnly === true,
      );
      expect(heatingGuards).toHaveLength(1);
      expect(heatingGuards[0].name).toContain("· WOOD-PELLET-ASSEMBLY · navigačný obrys");
      expect(heatingGuards[0].checkCollisions).toBe(true);
      expect(heatingGuards[0].isVisible).toBe(false);

      const serviceCoreWall = INTERIOR_WALLS.find(
        (wall) => wall.id === "IW-BATH-105-NORTH",
      )!;
      const serviceCoreWallMesh = scene.meshes.find((mesh) =>
        mesh.name.includes(`Vnútorná stena ${serviceCoreWall.id}`),
      );
      expect(serviceCoreWallMesh?.checkCollisions).toBe(true);
      expect(serviceCoreWallMesh?.isPickable).toBe(true);
      serviceCoreWallMesh?.computeWorldMatrix(true);
      expect(serviceCoreWallMesh?.position.z).toBeCloseTo(
        sceneZM((serviceCoreWall.rectMm.y0 + serviceCoreWall.rectMm.y1) / 2),
        8,
      );
      expect(
        (serviceCoreWallMesh?.getBoundingInfo().boundingBox.extendSizeWorld.z ?? 0) * 2,
      ).toBeCloseTo(140 * MM_TO_M, 8);

      const bathroomMeshes = scene.meshes.filter((mesh) =>
        mesh.name.startsWith(BATHROOM_FITOUT.id),
      );
      const bathroomGuards = bathroomMeshes.filter(
        (mesh) => mesh.metadata?.walkCollisionOnly === true,
      );
      expect(bathroomGuards).toHaveLength(3);
      expect(
        bathroomGuards.every((guard) => guard.checkCollisions && !guard.isVisible),
      ).toBe(true);
      const builtInGuard = bathroomGuards.find((guard) =>
        guard.name.includes("· BUILT-IN-2616 · hladký navigačný obrys"),
      );
      const oldBuiltInCenterYmm = (8322 + 8972) / 2;
      expect(builtInGuard?.position.z).toBeCloseTo(
        sceneZM(
          (BATHROOM_FITOUT.builtIn.footprintMm.y0 +
            BATHROOM_FITOUT.builtIn.footprintMm.y1) /
            2,
        ),
        8,
      );
      expect((builtInGuard?.position.z ?? 0) - sceneZM(oldBuiltInCenterYmm)).toBeCloseTo(
        0.2,
        8,
      );

      for (const appliance of BATHROOM_FITOUT.builtIn.appliances) {
        const body = bathroomMeshes.find((mesh) =>
          mesh.name.includes(`· ${appliance.kind} ·`),
        );
        expect(body, `${appliance.kind} renders in the laundry tower`).toBeDefined();
        body?.computeWorldMatrix(true);
        expect(body?.getBoundingInfo().boundingBox.minimumWorld.y).toBeCloseTo(
          appliance.baseElevationMm * MM_TO_M,
          6,
        );
        expect(body?.getBoundingInfo().boundingBox.maximumWorld.y).toBeCloseTo(
          (appliance.baseElevationMm + appliance.heightMm) * MM_TO_M,
          6,
        );
      }

      const radiatorCollectors = bathroomMeshes.filter((mesh) =>
        mesh.name.includes("· TOWEL-RADIATOR-600 · zvislý kolektor"),
      );
      const radiatorRungs = bathroomMeshes.filter((mesh) =>
        mesh.name.includes("· TOWEL-RADIATOR-600 · vodorovná priečka"),
      );
      expect(radiatorCollectors).toHaveLength(2);
      expect(radiatorRungs).toHaveLength(BATHROOM_FITOUT.towelRadiator.rungCount);
      expect(
        radiatorCollectors.every((mesh) => mesh.isPickable && !mesh.checkCollisions),
      ).toBe(true);
      const radiatorGuard = bathroomGuards.find((guard) =>
        guard.name.includes("· TOWEL-RADIATOR-600 · hladký navigačný obrys"),
      );
      expect(radiatorGuard).toBeDefined();
      expect(radiatorGuard?.position.z).toBeCloseTo(
        sceneZM(
          (BATHROOM_FITOUT.towelRadiator.footprintMm.y0 +
            BATHROOM_FITOUT.towelRadiator.footprintMm.y1) /
            2,
        ),
        8,
      );

      const wcGuards = scene.meshes.filter(
        (mesh) =>
          mesh.name.startsWith(WC_FITOUT.id) &&
          mesh.metadata?.walkCollisionOnly === true,
      );
      expect(wcGuards).toHaveLength(2);
      expect(wcGuards.every((guard) => guard.checkCollisions && !guard.isVisible)).toBe(true);
      const planSize = (mesh: AbstractMesh) => {
        mesh.computeWorldMatrix(true);
        const extent = mesh.getBoundingInfo().boundingBox.extendSizeWorld;
        return { x: extent.x * 2, z: extent.z * 2 };
      };
      const toiletGuard = wcGuards.find((mesh) =>
        mesh.name.includes("WALL-HUNG-WC"),
      )!;
      const basinGuard = wcGuards.find((mesh) =>
        mesh.name.includes("COMPACT-BASIN"),
      )!;
      const toiletGuardSize = planSize(toiletGuard);
      const basinGuardSize = planSize(basinGuard);
      expect(toiletGuardSize.x).toBeCloseTo(0.37, 8);
      expect(toiletGuardSize.z).toBeCloseTo(0.52, 8);
      expect(basinGuardSize.x).toBeCloseTo(0.25, 8);
      expect(basinGuardSize.z).toBeCloseTo(0.4, 8);

      const toiletBowl = scene.meshes.find((mesh) =>
        mesh.name.startsWith(WC_FITOUT.id)
        && mesh.name.includes("WALL-HUNG-WC · keramická misa"),
      )!;
      const basinBowl = scene.meshes.find((mesh) =>
        mesh.name.startsWith(WC_FITOUT.id)
        && mesh.name.includes("COMPACT-BASIN · keramické umývadlo 400 × 250"),
      )!;
      const toiletBowlSize = planSize(toiletBowl);
      const basinBowlSize = planSize(basinBowl);
      expect(toiletBowlSize.x).toBeCloseTo(0.37, 6);
      expect(toiletBowlSize.z).toBeCloseTo(0.52, 6);
      expect(basinBowlSize.x).toBeCloseTo(0.25, 6);
      expect(basinBowlSize.z).toBeCloseTo(0.4, 6);

      const garageMeshes = scene.meshes.filter((mesh) => mesh.name.startsWith(GARAGE_FITOUT.id));
      for (const required of [
        "· UTILITY-SINK ·",
        "· GARAGE-RACK ·",
        "· GARAGE-SHELF ·",
        "· PEGBOARD ·",
        "· GARAGE-CLUTTER ·",
        "· LONG-TOOL ·",
        "· MOWER ·",
      ]) {
        expect(
          garageMeshes.some((mesh) => mesh.name.includes(required)),
          `garage renders ${required}`,
        ).toBe(true);
      }

      expect(
        garageMeshes.find((mesh) => mesh.name.includes("hlboká nerezová pracovná vaňa"))
          ?.metadata,
      ).toMatchObject({
        designSourceId: GARAGE_FITOUT.sourceId,
        plumbingStatus: GARAGE_FITOUT.plumbingStatus,
      });
      expect(
        garageMeshes.filter((mesh) => mesh.name.includes("kartónová krabica")),
      ).toHaveLength(GARAGE_FITOUT.storageRack.cardboardBoxCount);
      expect(
        garageMeshes.filter((mesh) => mesh.name.includes("plastový box")),
      ).toHaveLength(GARAGE_FITOUT.storageRack.plasticBinCount);
      expect(
        garageMeshes.filter((mesh) => mesh.name.includes("plechovka farby")),
      ).toHaveLength(GARAGE_FITOUT.storageRack.paintCanCount);
      expect(
        garageMeshes.some(
          (mesh) =>
            mesh.name.includes("· REAR-SHELF ·") ||
            mesh.name.includes("· GARAGE-CLUTTER · zadný box"),
        ),
        "the garden-loggia door head stays free of rear shelves and stored boxes",
      ).toBe(false);
      expect(
        garageMeshes.filter((mesh) => /· MOWER · gumové koleso \d/.test(mesh.name)),
      ).toHaveLength(4);
      expect(
        garageMeshes.find((mesh) => mesh.name.includes("· MOWER · sklopná oceľová rukoväť"))
          ?.getTotalVertices(),
      ).toBeGreaterThan(0);

      const garageGuards = garageMeshes.filter(
        (mesh) => mesh.metadata?.walkCollisionOnly === true,
      );
      expect(garageGuards.map((guard) => guard.name)).toEqual(expect.arrayContaining([
        expect.stringContaining("· UTILITY-SINK · navigačný obrys"),
        expect.stringContaining("· GARAGE-RACK · navigačný obrys"),
        expect.stringContaining("· MOWER · navigačný obrys"),
      ]));
      expect(garageGuards).toHaveLength(3);
      expect(garageMeshes.filter((mesh) => mesh.checkCollisions)).toEqual(garageGuards);
      for (const guard of garageGuards) {
        expect(guard.checkCollisions).toBe(true);
        expect(guard.isVisible).toBe(false);
      }

      const garageCameraProxies = garageMeshes.filter(
        (mesh) => mesh.metadata?.cameraOcclusionProxy === true,
      );
      expect(garageCameraProxies.map((proxy) => proxy.name)).toEqual([
        expect.stringContaining("· GARAGE-RACK ·"),
        expect.stringContaining("· GARAGE-SHELF ·"),
      ]);
      for (const proxy of garageCameraProxies) {
        expect(proxy.metadata?.cameraOccluder).toBe(true);
        expect(proxy.isVisible).toBe(false);
        expect(proxy.isPickable).toBe(false);
        expect(proxy.checkCollisions).toBe(false);
      }
      expect(
        garageMeshes.find((mesh) => mesh.name.includes("· PEGBOARD · dierovaná stena"))
          ?.metadata?.cameraOccluder,
      ).toBe(true);
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });

  it("renders only the new cylindrical stove, curved glass and coaxial top connection", () => {
    const engine = new NullEngine({
      renderHeight: 256,
      renderWidth: 256,
      textureSize: 256,
    });
    const scene = new Scene(engine);
    const material = (name: string) => new PBRMaterial(name, scene);
    try {
      buildInterior({
        scene,
        anisotropy: 1,
        wall: material("test-wall"),
        soffit: material("test-soffit"),
        glassFrame: material("test-glass-frame"),
        chimneyMetal: material("test-chimney-metal"),
        timber: material("test-timber"),
        register: (mesh: AbstractMesh) => mesh,
        realisticOnly: (mesh: AbstractMesh) => mesh,
        castShadow: (mesh: AbstractMesh) => mesh,
      });

      const meshes = scene.meshes.filter((mesh) => mesh.name.startsWith(FIREPLACE_STOVE.id));
      const find = (marker: string) => meshes.find((mesh) => mesh.name.includes(marker));
      const body = find("· BODY ·");
      const glass = find("· CURVED-GLASS ·");

      expect(body).toBeDefined();
      expect(body?.checkCollisions).toBe(true);
      expect(body?.metadata).toMatchObject({
        designSourceId: FIREPLACE_STOVE.sourceId,
        fireplaceShape: "CYLINDRICAL",
        cameraOccluder: true,
      });
      body?.computeWorldMatrix(true);
      expect((body?.getBoundingInfo().boundingBox.extendSizeWorld.x ?? 0) * 2).toBeCloseTo(
        FIREPLACE_STOVE.bodyDiameterMm * 0.001,
        3,
      );
      expect((body?.getBoundingInfo().boundingBox.extendSizeWorld.z ?? 0) * 2).toBeCloseTo(
        FIREPLACE_STOVE.bodyDiameterMm * 0.001,
        3,
      );

      expect(glass).toBeDefined();
      expect(glass?.getTotalVertices()).toBeGreaterThan(100);
      expect(find("· FIRE-GLOW ·")).toBeDefined();
      expect(find("· DOOR-HANDLE ·")).toBeDefined();
      expect(find("· FLUE-COLLAR ·")).toBeDefined();
      expect(meshes.filter((mesh) => mesh.checkCollisions)).toEqual([body]);
      expect(
        scene.lights.some((light) => light.name.includes(`${FIREPLACE_STOVE.id} · FIRE-LIGHT`)),
      ).toBe(true);
      expect(
        scene.meshes.some((mesh) =>
          /komínový pilier|dymovod do komína|koleno dymovodu|Krbové kachle vedľa dverí/.test(
            mesh.name,
          ),
        ),
      ).toBe(false);
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
