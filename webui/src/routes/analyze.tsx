import React, { useState, useRef, useEffect } from "react";

import { TaskOutput } from "../models";
import { transTaskOutput } from "../models/util";
import { outputReadByName, outputGetVideoPreview } from "../client";

type Point = { x: number; y: number };

function RoiOnImage(props: {
  imgBlob: Blob;
  roi: Point[];
  onRoiChange?: (roi: Point[]) => void;
}) {
  const { imgBlob, roi, onRoiChange } = props;

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [draggingPoint, setDraggingPoint] = useState<number | null>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    const loadImage = async () => {
      if (!imgBlob) return;
      const img = new Image();
      img.src = URL.createObjectURL(imgBlob);
      img.onload = () => setImage(img);
    };
    loadImage();
  }, [imgBlob]);

  useEffect(() => {
    setPoints(roi);
  }, [roi]);

  useEffect(() => {
    if (image && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d")!;

      // 캔버스를 비움
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 이미지를 그림
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

      // 직선을 그림
      ctx.beginPath();
      ctx.setLineDash([5, 5]);
      ctx.moveTo(points[0].x, points[0].y);
      ctx.lineTo(points[1].x, points[1].y);
      ctx.lineTo(points[3].x, points[3].y);
      ctx.lineTo(points[2].x, points[2].y);
      ctx.lineTo(points[0].x, points[0].y);
      ctx.strokeStyle = "black";
      ctx.stroke();

      // 네 개의 점을 그림
      points.forEach((point, index) => {
        ctx.beginPath();
        ctx.setLineDash([]);
        ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);

        switch (index) {
          case 0:
            ctx.fillStyle = "red";
            break;
          case 1:
            ctx.fillStyle = "orange";
            break;
          case 2:
            ctx.fillStyle = "green";
            break;
          case 3:
            ctx.fillStyle = "blue";
            break;
        }
        ctx.fill();
        ctx.strokeStyle = "black";
        ctx.stroke();
      });
    }
  }, [image, points]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const { offsetX, offsetY } = e.nativeEvent;
    const pointIndex = points.findIndex((point) => {
      const dx = point.x - offsetX;
      const dy = point.y - offsetY;
      return Math.sqrt(dx * dx + dy * dy) < 10;
    });
    if (pointIndex !== -1) {
      setDraggingPoint(pointIndex);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (draggingPoint !== null) {
      const { offsetX, offsetY } = e.nativeEvent;
      const updatedPoints = points.map((point, index) =>
        index === draggingPoint ? { x: offsetX, y: offsetY } : point
      );
      setPoints(updatedPoints);
    }
  };

  const handleMouseUp = () => {
    setDraggingPoint(null);
    onRoiChange?.(points);
  };

  return (
    <canvas
      ref={canvasRef}
      width={720}
      height={480}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      className="rounded-md border border-gray-300"
    />
  );
}

function AnalyzePage() {
  const [csvName, setCsvName] = useState("");
  const [csvOutput, setCsvOutput] = useState<TaskOutput | null>(null);
  const [imgBlob, setImgBlob] = useState<Blob | null>(null);
  const [roi, setRoi] = useState<Point[]>([
    { x: 150, y: 150 }, // left top
    { x: 150, y: 250 }, // left bottom
    { x: 250, y: 150 }, // right top
    { x: 250, y: 250 }, // right bottom
  ]);

  useEffect(() => {
    if (csvOutput) {
      outputGetVideoPreview({
        path: { name: csvOutput.metadata["targetname"] },
      }).then((res) => {
        setImgBlob(res.data as Blob);
      });
    }
  }, [csvOutput]);

  return (
    <section>
      <h2 className="titlebox mb-4">차량 추적 데이터 분석하기</h2>
      <p className="descbox my-4">
        영상 차량 추적 데이터를 선택한 후 차량의 속도 등을 분석할 수 있습니다.
      </p>
      <div className="text-lg font-medium mb-2">
        객체 추적 결과 파일 이름{" "}
        <span className="text-sm text-gray-400">text/detection</span>
      </div>
      <div className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            className="inputbox flex-grow"
            value={csvName}
            onChange={(e) => setCsvName(e.target.value)}
          />
          <button
            className="btn-base btn-gray flex-none"
            onClick={async () => {
              try {
                if (!csvName) throw new Error("파일 이름을 입력해주세요.");
                const outputRes = await outputReadByName({
                  path: { name: csvName },
                });
                setCsvOutput(transTaskOutput(outputRes.data!));
              } catch (err) {
                if (err instanceof Error) alert(err.message);
              }
            }}
          >
            ROI 및 실제 거리 설정
          </button>
        </div>
        {imgBlob && (
          <div className="text-right mt-2 text-sm text-amber-800">
            위의 버튼을 다시 누르면 새로운 미리보기 이미지를 불러옵니다.
          </div>
        )}
      </div>
      <div className="text-lg font-medium mb-2">ROI 및 실제 거리 설정</div>
      {imgBlob && (
        <div className="mb-2 text-sm text-amber-800">
          아래의 미리보기 이미지에 있는 네 개의 점을 이동하여 ROI를 설정할 수
          있습니다.
        </div>
      )}
      <div className="flex gap-4 mb-4">
        <RoiOnImage
          imgBlob={imgBlob!}
          roi={roi}
          onRoiChange={(roi) => setRoi(roi)}
        />
        {csvOutput && (
          <div className="mb-4 space-y-2">
            {Object.entries(csvOutput.metadata).map(([key, value]) => (
              <div key={key}>
                <span className="inline-block bg-gray-600 text-gray-100 px-2.5 py-0.5 mb-0.5 rounded-md">
                  {key}
                </span>
                <div>{value}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div>
        <div className="grid grid-cols-6 space-x-2 mb-4">
          <div>
            <div className="font-medium mb-1 text-red-600">Left Top</div>
            <div className="inputbox bg-gray-50">{`(${roi[0].x}, ${roi[1].y})`}</div>
          </div>
          <div>
            <div className="font-medium mb-1 text-orange-600">Left Bottom</div>
            <div className="inputbox bg-gray-50">{`(${roi[1].x}, ${roi[1].y})`}</div>
          </div>
          <div>
            <div className="font-medium mb-1 text-green-600">Right Top</div>
            <div className="inputbox bg-gray-50">{`(${roi[2].x}, ${roi[2].y})`}</div>
          </div>
          <div>
            <div className="font-medium mb-1 text-blue-600">Right Bottom</div>
            <div className="inputbox bg-gray-50">{`(${roi[3].x}, ${roi[3].y})`}</div>
          </div>
          <div>
            <div className="font-medium mb-1">도로 가로 길이(m)</div>
            <input type="text" className="inputbox" />
          </div>
          <div>
            <div className="font-medium mb-1">도로 세로 길이(m)</div>
            <input type="text" className="inputbox" />
          </div>
        </div>
        <div className="text-right">
          <button className="btn-base btn-dark">분석하기</button>
        </div>
      </div>
      <p className="descbox my-4">
        영상 차량 추적 데이터 분석 결과는 아래에서 확인할 수 있습니다.
      </p>
    </section>
  );
}

export default AnalyzePage;
