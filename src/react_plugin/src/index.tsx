import * as React from "react";
import {
  FuncNodesReactPlugin,
  LATEST_VERSION,
  NodeHooksType,
  RenderPluginFactoryProps,
  RendererPlugin,
  NodeHooksProps,
  useIOStore,
  useSetIOValueOptions,
  useIOValueStore,
  useSetIOValue,
} from "@linkdlab/funcnodes-react-flow-plugin";

const renderpluginfactory = ({}: RenderPluginFactoryProps) => {
  const WebCamHook: NodeHooksType = ({}: NodeHooksProps) => {
    const [stream, setStream] = React.useState<MediaStream | null>(null);
    const delay_io_store = useIOValueStore("delay_ms");
    const quality_io_store = useIOValueStore("quality");
    const src_io_store = useIOValueStore("src");
    const set_imagedata_io_value = useSetIOValue("imagedata");
    const set_src_value_options = useSetIOValueOptions("src");

    React.useEffect(() => {
      async function initWebcam() {
        const value = src_io_store?.preview?.value;
        if (value === null || value === undefined || value === "null") {
          setStream(null);
          return;
        }
        try {
          //setStream(await navigator.mediaDevices.getUserMedia({ video: true }));
          setStream(
            await navigator.mediaDevices.getUserMedia({
              video: { deviceId: { exact: value.toString() } },
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
    }, [src_io_store]);

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
        set_src_value_options({
          values: ids,
          keys: labels,
          nullable: true,
        });
      }
      updateOptions();
    }, [set_src_value_options]);

    React.useEffect(() => {
      if (!stream) return;
      const quality = quality_io_store?.preview;
      const delay_ms = delay_io_store?.preview;
      if (quality === undefined || delay_ms === undefined) return;
      let quality_value = parseFloat((quality.value ?? 70).toString());
      if (isNaN(quality_value)) quality_value = 70;
      if (quality_value < 0) quality_value = 0;
      if (quality_value > 100) quality_value = 100;

      let delay_ms_value = parseFloat((delay_ms.value ?? 1000).toString());
      if (isNaN(delay_ms_value)) delay_ms_value = 1000;
      if (delay_ms_value < 0) delay_ms_value = 0;

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

            set_imagedata_io_value(
              {
                width: canvas.width,
                height: canvas.height,
                data: base64,
              },

              false
            );
          },
          "image/jpeg",
          quality_value / 100
        );
      }, delay_ms_value); // capture one frame per second; adjust if needed
      return () => {
        clearInterval(interval);
        video.pause();
        video.srcObject = null;
      };
    }, [stream, quality_io_store, delay_io_store, set_imagedata_io_value]);

    return <></>;
  };

  const MyRendererPlugin: RendererPlugin = {
    handle_preview_renderers: {},
    data_overlay_renderers: {},
    data_preview_renderers: {},
    data_view_renderers: {},
    input_renderers: {},
    node_hooks: { "webcam.browserwebcam": [WebCamHook] },
  };

  return MyRendererPlugin;
};

const Plugin: FuncNodesReactPlugin = {
  renderpluginfactory: renderpluginfactory,
  v: LATEST_VERSION,
};

export default Plugin;
