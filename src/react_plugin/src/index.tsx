import { latest_types } from "@linkdlab/funcnodes_react_flow";

const renderpluginfactory = ({
  React,
  fnrf_zst,
}: latest_types.RenderPluginFactoryProps) => {
  const WebCamHook: latest_types.NodeHooksType = ({
    nodecontext,
  }: latest_types.NodeHooksProps) => {
    const [stream, setStream] = React.useState<MediaStream | null>(null);
    const { preview: delay_ms } = nodecontext.node_data.io[
      "delay_ms"
    ]?.valuestore() || {
      preview: { value: 1000 },
    };
    const { preview: quality } = nodecontext.node_data.io[
      "quality"
    ]?.valuestore() || {
      preview: { value: 70 },
    };

    const { preview: src } = nodecontext.node_data.io["src"]?.valuestore() || {
      preview: { value: null },
    };

    React.useEffect(() => {
      async function initWebcam() {
        const value = src?.value;
        if (value === null || value === undefined || value === "null") {
          setStream(null);
          return;
        }
        try {
          //setStream(await navigator.mediaDevices.getUserMedia({ video: true }));
          setStream(
            await navigator.mediaDevices.getUserMedia({
              video: { deviceId: { exact: value } },
            })
          );
          // Set up an interval to capture a frame (adjust interval as needed)
        } catch (error) {
          console.error("Error accessing webcam:", error);
          setStream(null);
        }
      }
      initWebcam();
      return () => {
        if (stream) {
          stream.getTracks().forEach((track) => track.stop());
        }
      };
    }, [src]);

    React.useEffect(() => {
      async function updateOptions() {
        await navigator.mediaDevices.getUserMedia({ video: true });

        const devices = await navigator.mediaDevices.enumerateDevices();

        const ids: string[] = [];
        const labels: string[] = [];
        for (var i = 0; i < devices.length; i++) {
          var device = devices[i];
          if (device.kind === "videoinput") {
            ids.push(device.deviceId);
            labels.push(device.label || "camera " + (i + 1));
          }
        }
        fnrf_zst.worker?._send_cmd({
          cmd: "update_io_value_options",
          kwargs: {
            nid: nodecontext.node_data.id,
            ioid: "src",
            options: {
              options: {
                type: "enum",
                values: ids,
                keys: labels,
                nullable: true,
              },
            },
          },
        });
      }
      updateOptions();
    }, []);

    React.useEffect(() => {
      if (!stream) return;
      if (quality === undefined || delay_ms === undefined) return;
      const video = document.createElement("video");
      video.srcObject = stream;
      video.play().catch(() => {});
      const canvas = document.createElement("canvas");
      const interval = setInterval(async () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          async (blob) => {
            if (!blob) return;
            const arrayBuffer = await blob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64 = btoa(
              uint8Array.reduce(
                (acc, byte) => acc + String.fromCharCode(byte),
                ""
              )
            );
            fnrf_zst.worker?.set_io_value({
              nid: nodecontext.node_data.id,
              ioid: "imagedata",
              value: {
                width: canvas.width,
                height: canvas.height,
                data: base64,
              },
              set_default: false,
            });
          },
          "image/jpeg",
          quality.value / 100
        );
      }, delay_ms.value); // capture one frame per second; adjust if needed
      return () => {
        clearInterval(interval);
        video.pause();
        video.srcObject = null;
      };
    }, [stream, quality, delay_ms]);
  };

  const MyRendererPlugin: latest_types.RendererPlugin = {
    handle_preview_renderers: {},
    data_overlay_renderers: {},
    data_preview_renderers: {},
    data_view_renderers: {},
    input_renderers: {},
    node_context_extenders: {},
    node_hooks: { "webcam.browserwebcam": [WebCamHook] },
  };

  return MyRendererPlugin;
};

const Plugin: latest_types.FuncNodesReactPlugin = {
  renderpluginfactory: renderpluginfactory,
  v: 1,
};

export default Plugin;
