import { Outlet, Link } from "react-router-dom";

import {
  VideocamOutlined as VideoCamIcon,
  GpsFixedOutlined as GpsFixedIcon,
  TimelineOutlined as TimelineIcon,
} from "@mui/icons-material";

import exRoadLogoImg from "../assets/ex-road-logo.png";
import uosLogoImg from "../assets/uos-logo.png";
import ericaLogoImg from "../assets/erica-logo.png";

function RootPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="container mb-4">
        <div className="flex justify-between items-center">
          <h1 className="py-8 font-bold text-3xl">
            <Link to="/">고속도로 CCTV 영상 분석 시스템</Link>
          </h1>
          <div className="space-x-4 [&>img]:h-4 [&>img]:inline-block lg:[&>img]:h-6">
            <img src={exRoadLogoImg} alt="exRoad Logo" />
            <img src={ericaLogoImg} alt="ERICA Logo" />
            <img src={uosLogoImg} alt="UOS Logo" />
          </div>
        </div>
        <nav className="flex gap-6 text-lg font-medium">
          <Link to="/record" className="flex items-center hover:underline">
            <VideoCamIcon className="mr-1" />
            CCTV 녹화하기
          </Link>
          <Link to="/track" className="flex items-center hover:underline">
            <GpsFixedIcon className="mr-1" />
            CCTV 영상 차량 추적하기
          </Link>
          <Link to="/analyze" className="flex items-center hover:underline">
            <TimelineIcon className="mr-1" />
            차량 추적 데이터 분석하기
          </Link>
        </nav>
      </header>
      <main className="container">
        <Outlet />
      </main>
      {/* footer */}
      <footer className="mb-8"></footer>
    </div>
  );
}

export default RootPage;
