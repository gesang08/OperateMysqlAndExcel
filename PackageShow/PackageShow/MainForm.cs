using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using Microsoft.VisualBasic;
using MySql.Data.MySqlClient;
using System.Text.RegularExpressions;//引用正则表达式模块
//git submit

namespace PackageShow
{
    public partial class PackageShowFormClass : Form
    {
        /**************************************类内全局变量声明**************************************/
        /// <summary>
        /// 从数据库读取信息存储声明
        /// </summary>
        string ap_id = null;
        string current_row_ap_id = null;//存放当前点击DataGridView中行所在的打包工单号
        uint total_layer = 0, total_plate = 0;
        float total_area = 0;
        bool error_flag = false;//记录出错异常程序
        int current_layer = 1;//记录通过LEFT和RIGHT键操作，当前所属哪一层
        uint current_total_plates = 0;
        List<int> each_layer_total_plates = new List<int>();//存放每层的块数,Count=10
        List<string> info_position = new List<string>();//存放每层每块信息，,Count=100
        int Long = 0, Short = 0;
        /// <summary>
        /// 数据库变量声明
        /// </summary>
        string management_db = Properties.PackageConfig.Default.ManagementDB;
        string manufacture_db = Properties.PackageConfig.Default.ManufactureDB;
        string database_ip = Properties.PackageConfig.Default.ServerIP;
        string database_user = Properties.PackageConfig.Default.UserName;
        string database_password = Properties.PackageConfig.Default.Password;
        string charset="utf8";
        MySqlConnection mysql;//用于打开、关闭数据库
        /// <summary>
        /// 画板子，写尺寸字符等方面的声明
        /// </summary>
        int windows_height, windows_width;
        Graphics box_bed;//定义Graphics对象，该对象用于画平面范围框架和部件
        Brush brush_black = new SolidBrush(Color.Black);//定义实心画笔的颜色对象为黑色，这个用于画部件及尺寸字体颜色
        float box_x = 0;
        float box_y = 0;
        float box_width = 0;//平面范围宽
        float box_height = 0;//平面范围高
        float width_scale_ratio = 0, height_scale_ratio = 0;//高宽相对于屏幕缩放比例
        float x = 0, y = 0, width = 0, height = 0;
        int is_change = 0;

        /****************************************事件响应****************************************/
        /// <summary>
        /// 加载窗体时响应的事件
        /// </summary>
        public PackageShowFormClass()
        {
            InitializeComponent();
            FormBorderStyle = FormBorderStyle.None;//设置窗体为无边框格式
            WindowState = FormWindowState.Maximized;//设置窗体为最大化
            GunReturnText.TabIndex = 0;//用TAB键的index值设置初始焦点在GunReturnText上
            init_componet_postion();//窗体控件布局与自定调整方法
            mysql = getMySqlCon();
            GunReturnText.Visible = false;
            get_info_package_from_db();
        }

        /// <summary>
        /// 用于握式扫码枪扫描员工条码、板子条码、相关设置setup的响应事件
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void GunReturnText_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((int)e.KeyChar == 13)
            {
                process_code(GunReturnText.Text.ToString());
                GunReturnText.Clear();
            }
        }

        /// <summary>
        /// 在DataGridView里点击一下当前包所在的行数，将该包一层层显示出来
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void info_package_CellMouseClick(object sender, DataGridViewCellMouseEventArgs e)
        {
            current_row_ap_id = null;//存放当前点击DataGridView中行所在的打包工单号
            current_layer = 1;//清空当前层为1
            current_total_plates = 0;//把当前包总块数置为0
            int current_row_index = info_package.CurrentCell.RowIndex;
            if (current_row_index < 0)
            {
                current_row_ap_id = null;
            }
            else
            {
                if (!error_flag)
                {
                    //每次点击一包都需要把存储上一包的内存信息清空
                    each_layer_total_plates.Clear();
                    info_position.Clear();
                    Long = 0;
                    Short = 0;

                    current_row_ap_id = info_package.Rows[current_row_index].Cells[0].Value.ToString();//获取当前选中行的工单号
                    total_layer = Convert.ToUInt32(info_package.Rows[current_row_index].Cells[1].Value);
                    current_total_plates = Convert.ToUInt32(info_package.Rows[current_row_index].Cells[3].Value);
                    this.package_label.Text = current_row_ap_id + "包第" + current_layer.ToString() + "层";
                    this.PartInfoLabel.Text = current_row_ap_id + "包部件信息：";
                    get_position_info(current_row_ap_id);
                    if (!error_flag)
                    {
                        show_first_layer();
                        show_part_info();
                    }
                }
                
            }

        }

      
        /// <summary>
        /// 键盘上“←键”按下显示上一层，“→键”按下显示下一层
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void PackageShowFormClass_KeyDown(object sender, KeyEventArgs e)
        {
            switch (e.KeyCode)
            {
                case Keys.Right://显示下一层
                    if (current_layer <= total_layer)
                    {
                        if (current_layer == total_layer)//到了最后一层
                        {
                            MessageBox.Show(current_row_ap_id + "包的最后一层！");
                        }
                        else
                        {
                            current_layer++;
                            this.package_label.Text = current_row_ap_id + "包第" + current_layer.ToString() + "层";
                            this.show_next_layer();
                        }
                    }
                    break;
                case Keys.Left://显示上一层
                    if (current_layer >= 1)
                    {
                        if (current_layer == 1)
                        {
                            MessageBox.Show(current_row_ap_id + "包的第一层！");
                        }
                        else
                        {
                            current_layer--;
                            this.package_label.Text = current_row_ap_id + "包第" + current_layer.ToString() + "层";
                            this.show_before_layer();
                        }   
                    }
                    break;
                case Keys.Escape:
                    System.Environment.Exit(0);
                    break;
                default:
                    break;
            }
        }
        /****************************************相关方法****************************************/
        public void init_componet_postion()
        {
            box_bed = this.CreateGraphics();
            windows_height = Screen.GetBounds(this).Height;
            windows_width = Screen.GetBounds(this).Width;
            FactoryStation.Text = Properties.PackageConfig.Default.FactoryName + "-" + Properties.PackageConfig.Default.WorkStation;
            FactoryStation.Location = new Point(windows_width/2 - FactoryStation.Size.Width/2,0);
            package_label.Location = new Point(windows_width - 250, FactoryStation.Size.Height);
            info_package.Size = new Size(info_package.Width, 400);
            PartInfoDataGridView.Size = new Size(PartInfoDataGridView.Width, 400);
            PartInfoDataGridView.Location = new Point(info_package.Location.X,info_package.Location.Y + info_package.Size.Height + 70);
            PartInfoLabel.Location = new Point(PartInfoDataGridView.Location.X,PartInfoDataGridView.Location.Y - PartInfoLabel.Size.Height-4);
        }

        /// <summary>
        /// 与数据库相关的设置
        /// </summary>
        public void setup()
        {
            management_db = Properties.PackageConfig.Default.ManagementDB;
            manufacture_db = Properties.PackageConfig.Default.ManufactureDB;
            database_ip = Properties.PackageConfig.Default.ServerIP;
            database_user = Properties.PackageConfig.Default.UserName;
            database_password = Properties.PackageConfig.Default.Password;
            database_ip = Interaction.InputBox("请输入服务器IP", "数据库服务器修改", database_ip, 100, 100);
            Properties.PackageConfig.Default.ServerIP = database_ip;
            management_db = Interaction.InputBox("请输入数据库名", "management数据库服务器修改", management_db, 100, 100);
            Properties.PackageConfig.Default.ManagementDB = management_db;
            manufacture_db = Interaction.InputBox("请输入数据库名", "manufacture数据库服务器修改", manufacture_db, 100, 100);
            Properties.PackageConfig.Default.ManufactureDB = manufacture_db;
            database_user = Interaction.InputBox("请输入登陆用户名", "数据库服务器修改", database_user, 100, 100);
            Properties.PackageConfig.Default.UserName = database_user;
            database_password = Interaction.InputBox("请输入登陆密码", "数据库服务器修改", database_password, 100, 100);
            Properties.PackageConfig.Default.Password = database_password;
            Properties.PackageConfig.Default.Save();
        }

        /// <summary>
        /// 用于扫码，设置，退出相关处理方法
        /// </summary>
        /// <param name="code扫码枪或工作人员输入的信息"></param>
        public void process_code(string code)
        {
            if (code.Contains("SETUP") || code.Contains("setup"))
            {
                setup();
            }
            else if (code.Contains("EXIT") || code.Contains("exit"))
            {
                System.Environment.Exit(0);
            }
                
        }

        /// <summary>
        /// 获取work_package_task_list表中State=0的工单
        /// </summary>
        public void get_info_package_from_db()
        {
            this.info_package.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;//设置DataGridView的行列为自动调整
            String PackageSql = "SELECT `Ap_id`,`Total_plies`,`Total_area_gs`,`Package_num` FROM `work_package_task_list` WHERE `State` = 0";
            MySqlCommand InfoPackageCommand = getSqlCommand(PackageSql, mysql);
            try
            {
                mysql.Open();
                MySqlDataReader InfoPackageRead = InfoPackageCommand.ExecuteReader();
                if (InfoPackageRead.HasRows)
                {
                    while (InfoPackageRead.Read())
                    {
                        ap_id = InfoPackageRead.GetString(0);
                        total_layer = InfoPackageRead.GetUInt32(1);
                        total_area = InfoPackageRead.GetFloat(2);
                        total_plate = InfoPackageRead.GetUInt32(3);
                        string[] toshow = new string[] { ap_id, total_layer.ToString(),total_area.ToString(),total_plate.ToString()};
                        int rows = this.info_package.Rows.Add();
                        for (int i = 0; i < info_package.ColumnCount; i++)//把包信息显示到DataGridView里面
                        {
                            info_package.Rows[rows].Cells[i].Value = toshow[i];
                        }
                    }
                }
            }
            catch (MySqlException ex)
            {
                Console.WriteLine(DateTime.Now + "  get_info_package_from_db()方法中MySqlException Error:" + ex.ToString());
                error_flag = true;
            }
            finally
            {
                mysql.Close();
            }
        }

       /// <summary>
        /// 把当前包的所有部件信息显示出来
       /// </summary>
        public void show_part_info()
        {
            this.PartInfoDataGridView.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;//设置DataGridView的行列为自动调整
            this.PartInfoDataGridView.Rows.Clear();
            int index_row = 0;
            String PartInfoQuery = "SELECT `Part_id`,`Door_height`,`Door_width`,`Door_thick` FROM `order_part_online` WHERE `Package_task_list_ap_id` = '" + current_row_ap_id + "'";
            MySqlCommand PartInfoCommand = getSqlCommand(PartInfoQuery, mysql);
            try
            {
                mysql.Open();
                MySqlDataReader PartInfoReader = PartInfoCommand.ExecuteReader();
                if (PartInfoReader.HasRows)
                {
                    while (PartInfoReader.Read())
                    {
                        index_row++;
                        string[] toshow = new string[] {index_row.ToString(), PartInfoReader.GetString(0), PartInfoReader.GetFloat(1).ToString(), PartInfoReader.GetFloat(2).ToString(), PartInfoReader.GetInt32(3).ToString()};
                        int rows = this.PartInfoDataGridView.Rows.Add();
                        for (int i = 0; i < PartInfoDataGridView.ColumnCount; i++)//把包信息显示到DataGridView里面
                        {
                            PartInfoDataGridView.Rows[rows].Cells[i].Value = toshow[i];
                        }
                    }
                }
            }
            catch (MySqlException ex)
            {
                Console.WriteLine(DateTime.Now + "  show_part_info()方法中MySqlException Error:" + ex.ToString());
                error_flag = true;
            }
            finally
            {
                mysql.Close();
            }
        }

        public void get_position_info(string current_ap_id)
        {
            String PositionSql = "SELECT `Long`,`Short`,"+
                "`Num_plies1`,  LEFT(`Plies1_element_information1`, 256),  LEFT(`Plies1_element_information2`, 256),  LEFT(`Plies1_element_information3`, 256),  LEFT(`Plies1_element_information4`, 256),  LEFT(`Plies1_element_information5`, 256),  LEFT(`Plies1_element_information6`, 256),  LEFT(`Plies1_element_information7`, 256),  LEFT(`Plies1_element_information8`, 256),  LEFT(`Plies1_element_information9`, 256),  LEFT(`Plies1_element_information10`, 256), " +
                "`Num_plies2`,  LEFT(`Plies2_element_information1`, 256),  LEFT(`Plies2_element_information2`, 256),  LEFT(`Plies2_element_information3`, 256),  LEFT(`Plies2_element_information4`, 256),  LEFT(`Plies2_element_information5`, 256),  LEFT(`Plies2_element_information6`, 256),  LEFT(`Plies2_element_information7`, 256),  LEFT(`Plies2_element_information8`, 256),  LEFT(`Plies2_element_information9`, 256),  LEFT(`Plies2_element_information10`, 256)," +
                "`Num_plies3`,  LEFT(`Plies3_element_information1`, 256),  LEFT(`Plies3_element_information2`, 256),  LEFT(`Plies3_element_information3`, 256),  LEFT(`Plies3_element_information4`, 256),  LEFT(`Plies3_element_information5`, 256),  LEFT(`Plies3_element_information6`, 256),  LEFT(`Plies3_element_information7`, 256),  LEFT(`Plies3_element_information8`, 256),  LEFT(`Plies3_element_information9`, 256),  LEFT(`Plies3_element_information10`, 256), " +
                "`Num_plies4`,  LEFT(`Plies4_element_information1`, 256),  LEFT(`Plies4_element_information2`, 256),  LEFT(`Plies4_element_information3`, 256),  LEFT(`Plies4_element_information4`, 256),  LEFT(`Plies4_element_information5`, 256),  LEFT(`Plies4_element_information6`, 256),  LEFT(`Plies4_element_information7`, 256),  LEFT(`Plies4_element_information8`, 256),  LEFT(`Plies4_element_information9`, 256),  LEFT(`Plies4_element_information10`, 256)," +
                "`Num_plies5`,  LEFT(`Plies5_element_information1`, 256),  LEFT(`Plies5_element_information2`, 256),  LEFT(`Plies5_element_information3`, 256),  LEFT(`Plies5_element_information4`, 256),  LEFT(`Plies5_element_information5`, 256),  LEFT(`Plies5_element_information6`, 256),  LEFT(`Plies5_element_information7`, 256),  LEFT(`Plies5_element_information8`, 256),  LEFT(`Plies5_element_information9`, 256),  LEFT(`Plies5_element_information10`, 256), " +
                "`Num_plies6`,  LEFT(`Plies6_element_information1`, 256),  LEFT(`Plies6_element_information2`, 256),  LEFT(`Plies6_element_information3`, 256),  LEFT(`Plies6_element_information4`, 256),  LEFT(`Plies6_element_information5`, 256),  LEFT(`Plies6_element_information6`, 256),  LEFT(`Plies6_element_information7`, 256),  LEFT(`Plies6_element_information8`, 256),  LEFT(`Plies6_element_information9`, 256),  LEFT(`Plies6_element_information10`, 256)," +
                "`Num_plies7`,  LEFT(`Plies7_element_information1`, 256),  LEFT(`Plies7_element_information2`, 256),  LEFT(`Plies7_element_information3`, 256),  LEFT(`Plies7_element_information4`, 256),  LEFT(`Plies7_element_information5`, 256),  LEFT(`Plies7_element_information6`, 256),  LEFT(`Plies7_element_information7`, 256),  LEFT(`Plies7_element_information8`, 256),  LEFT(`Plies7_element_information9`, 256),  LEFT(`Plies7_element_information10`, 256), " +
                "`Num_plies8`,  LEFT(`Plies8_element_information1`, 256),  LEFT(`Plies8_element_information2`, 256),  LEFT(`Plies8_element_information3`, 256),  LEFT(`Plies8_element_information4`, 256),  LEFT(`Plies8_element_information5`, 256),  LEFT(`Plies8_element_information6`, 256),  LEFT(`Plies8_element_information7`, 256),  LEFT(`Plies8_element_information8`, 256),  LEFT(`Plies8_element_information9`, 256),  LEFT(`Plies8_element_information10`, 256)," +
                "`Num_plies9`,  LEFT(`Plies9_element_information1`, 256),  LEFT(`Plies9_element_information2`, 256),  LEFT(`Plies9_element_information3`, 256),  LEFT(`Plies9_element_information4`, 256),  LEFT(`Plies9_element_information5`, 256),  LEFT(`Plies9_element_information6`, 256),  LEFT(`Plies9_element_information7`, 256),  LEFT(`Plies9_element_information8`, 256),  LEFT(`Plies9_element_information9`, 256),  LEFT(`Plies9_element_information10`, 256), " +
                "`Num_plies10`,  LEFT(`Plies10_element_information1`, 256),  LEFT(`Plies10_element_information2`, 256),  LEFT(`Plies10_element_information3`, 256),  LEFT(`Plies10_element_information4`, 256),  LEFT(`Plies10_element_information5`, 256),  LEFT(`Plies10_element_information6`, 256),  LEFT(`Plies10_element_information7`, 256),  LEFT(`Plies10_element_information8`, 256),  LEFT(`Plies10_element_information9`, 256),  LEFT(`Plies10_element_information10`, 256)" +
                "FROM `work_package_task_list` WHERE `Ap_id` = '"+current_ap_id+"'";//读取数据库当前包的位置信息
            MySqlCommand InfoPositionCommand = getSqlCommand(PositionSql, mysql);
            try
            {
                mysql.Open();
                MySqlDataReader InfoPositionRead = InfoPositionCommand.ExecuteReader();
                if (InfoPositionRead.HasRows)
                {
                    if (InfoPositionRead.Read())
                    {
                        for (int i = 0; i < InfoPositionRead.FieldCount; i++)
                        {
                            switch (i)
                            { 
                                case 0:
                                    Long = InfoPositionRead.GetInt32(0);
                                    break;
                                case 1:
                                    Short = InfoPositionRead.GetInt32(1);
                                    break;
                                default:
                                    if (InfoPositionRead[InfoPositionRead.GetName(i)] != DBNull.Value)//处理数据库字段为NULL的方法
                                    {
                                        if (IsInt(InfoPositionRead.GetString(i)))
                                        {
                                            each_layer_total_plates.Add(InfoPositionRead.GetInt32(i));
                                        }
                                        else
                                        {
                                            info_position.Add(InfoPositionRead.GetString(i));
                                        }
                                    }
                                    else
                                    {
                                        info_position.Add(null);
                                    }
                                    break;
                            }
                        }
                    }
                }
            }
            catch (MySqlException ex)
            {
                Console.WriteLine(DateTime.Now + "  get_info_package_from_db()方法中MySqlException Error:" + ex.ToString());
                error_flag = true;
            }
            finally
            {
                mysql.Close();
            }
        }

        /// <summary>
        /// 在DataGridView中点击一包，把该包的第一层显示出来
        /// </summary>
        public void show_first_layer()
        {
            this.draw_main_frame();
            current_layer = 1;
            string first_layer_info = null;
            float temp = 0;
            for (int plate = 0; plate < each_layer_total_plates[current_layer-1]; plate++)//循环第一层
            {
                first_layer_info = info_position[plate];
                x = Convert.ToSingle(first_layer_info.Split('&')[0]);
                y = Convert.ToSingle(first_layer_info.Split('&')[1]);
                height = Convert.ToSingle(first_layer_info.Split('&')[2]);
                width = Convert.ToSingle(first_layer_info.Split('&')[3]);
                is_change = Convert.ToInt32(first_layer_info.Split('&')[4]);
                if (is_change == 1)//height对应windows_width
                {
                    temp = height;
                    height =width;
                    width = temp;
                }
                box_bed.DrawRectangle(new Pen(new SolidBrush(Color.Black), 6), box_x + x / width_scale_ratio, box_y + y / height_scale_ratio, height / width_scale_ratio, width / height_scale_ratio);
                Font myFont = new Font("宋体", change_font_size(Math.Min(width,height)), FontStyle.Bold);
                StringFormat str_format = new StringFormat();
                str_format.Alignment = StringAlignment.Center;
                str_format.LineAlignment = StringAlignment.Center;
                box_bed.DrawString(font_horizon_or_vertical(is_change,height,width), myFont, brush_black, box_x + x / width_scale_ratio + height / (width_scale_ratio * 2), box_y + y / height_scale_ratio + width / (height_scale_ratio * 2), str_format);
                }    
        }

        /// <summary>
        /// 按“→键”显示下一层的位置信息；注意：这边在显示上一层，下一层信息的时候，需要把DataGridView点击事件封锁，否则会有问题
        /// </summary>
        public void show_next_layer()
        {
            this.draw_main_frame();
            string next_layer_info = null;
            float temp = 0;
            for (int plate = 0; plate < each_layer_total_plates[current_layer - 1]; plate++)//循环第一层
            {
                next_layer_info = info_position[plate];
                x = Convert.ToSingle(next_layer_info.Split('&')[0]);
                y = Convert.ToSingle(next_layer_info.Split('&')[1]);
                height = Convert.ToSingle(next_layer_info.Split('&')[2]);
                width = Convert.ToSingle(next_layer_info.Split('&')[3]);
                is_change = Convert.ToInt32(next_layer_info.Split('&')[4]);
                if (is_change == 1)//height对应windows_width
                {
                    temp = height;
                    height = width;
                    width = temp;
                }
                box_bed.DrawRectangle(new Pen(new SolidBrush(Color.Black), 6), box_x + x / width_scale_ratio, box_y + y / height_scale_ratio, height / width_scale_ratio, width / height_scale_ratio);
                Font myFont = new Font("宋体", change_font_size(Math.Min(width, height)), FontStyle.Bold);
                StringFormat str_format = new StringFormat();
                str_format.Alignment = StringAlignment.Center;
                str_format.LineAlignment = StringAlignment.Center;
                box_bed.DrawString(font_horizon_or_vertical(is_change, height, width), myFont, brush_black, box_x + x / width_scale_ratio + height / (width_scale_ratio * 2), box_y + y / height_scale_ratio + width / (height_scale_ratio * 2), str_format);
            }    
        }

        /// <summary>
        /// 按“←键”显示下一层的位置信息
        /// </summary>
        public void show_before_layer()
        {
            this.draw_main_frame();
            string next_layer_info = null;
            float temp = 0;
            for (int plate = 0; plate < each_layer_total_plates[current_layer-1]; plate++)//循环第一层
            {
                next_layer_info = info_position[plate];
                x = Convert.ToSingle(next_layer_info.Split('&')[0]);
                y = Convert.ToSingle(next_layer_info.Split('&')[1]);
                height = Convert.ToSingle(next_layer_info.Split('&')[2]);
                width = Convert.ToSingle(next_layer_info.Split('&')[3]);
                is_change = Convert.ToInt32(next_layer_info.Split('&')[4]);
                if (is_change == 1)//height对应windows_width
                {
                    temp = height;
                    height = width;
                    width = temp;
                }
                box_bed.DrawRectangle(new Pen(new SolidBrush(Color.Black), 6), box_x + x / width_scale_ratio, box_y + y / height_scale_ratio, height / width_scale_ratio, width / height_scale_ratio);
                Font myFont = new Font("宋体", change_font_size(Math.Min(width, height)), FontStyle.Bold);
                StringFormat str_format = new StringFormat();
                str_format.Alignment = StringAlignment.Center;
                str_format.LineAlignment = StringAlignment.Center;
                box_bed.DrawString(font_horizon_or_vertical(is_change, height, width), myFont, brush_black, box_x + x / width_scale_ratio + height / (width_scale_ratio * 2), box_y + y / height_scale_ratio + width / (height_scale_ratio * 2), str_format);
            }    
        }

        public void draw_position(int box_long, int box_short, List<int> each_layer_total_plates, List<string> info_position)
        {
            /*协议：x & y & height & width & is_change & part_id
                is_change：low_x_length,low_y_length是否转变，0为不转变，1为转变
             */
            string part_position_info = null;
            float width_scale_ratio = 0, height_scale_ratio = 0;//高宽相对于屏幕缩放比例
            float x = 0, y = 0, width = 0, height = 0;
            int is_change = 0;
            

            //这里较长的x轴（屏幕宽）用来显示较长的部件高；这里较短的y轴（屏幕高）用来显示较短的部件宽；
            for (int layer = 0; layer < total_layer; layer++)//循环每层
            {
                for (int plate = 0; plate < each_layer_total_plates[layer]; plate++)//循环每层下每块
                {
                    part_position_info = info_position[layer * 10 + plate];
                    x = Convert.ToSingle(part_position_info.Split('&')[0]);
                    y = Convert.ToSingle(part_position_info.Split('&')[1]);
                    height = Convert.ToSingle(part_position_info.Split('&')[2]);
                    width = Convert.ToSingle(part_position_info.Split('&')[3]);
                    //is_change = Convert.ToInt32(part_position_info.Split('&')[4]);
                    width_scale_ratio = height / box_width;
                    height_scale_ratio = width / box_height;
                    if (width_scale_ratio > 1 || height_scale_ratio > 1)
                    {
                        height = height / width_scale_ratio;
                        width = width / height_scale_ratio;
                    }
                    box_bed.DrawRectangle(new Pen(new SolidBrush(Color.Black), 5), box_x + x, box_y + y, height, width);

                    Font myFont = new Font("宋体", 20, FontStyle.Bold);
                    
                    StringFormat str_format = new StringFormat();
                    str_format.Alignment = StringAlignment.Center;
                    str_format.LineAlignment = StringAlignment.Center;
                    box_bed.DrawString(height.ToString() + "×" + width.ToString(), myFont, brush_black, box_x + x + height / 2, box_y + y + width / 2, str_format);
                    
                }
            }       
        }

        public void draw_main_frame()
        {
            //画放板子的平面范围框架
            box_x = package_label.Location.X + package_label.Size.Width + 6;
            box_y = package_label.Location.Y + package_label.Size.Height + 6;
            //box_width = windows_width - box_x;//平面范围宽
            //box_height = windows_height - box_y;//平面范围高
            box_x = info_package.Size.Width + 20;
            box_y = FactoryStation.Size.Height + 20;
            box_width = windows_width - box_x;//平面范围宽
            box_height = windows_height - box_y;//平面范围高
            box_bed.FillRectangle(new SolidBrush(Color.FromArgb(255, 199, 237, 204)), box_x, box_y, box_width, box_height);
            box_bed.DrawRectangle(new Pen(new SolidBrush(Color.Black), 6), box_x, box_y, box_width, box_height);

            if (Long > box_width && Short > box_height)
            {
                width_scale_ratio = Long / box_width;//width_scale_ratio>1
                height_scale_ratio = Short / box_height;
            }
            else if (Long > box_width && Short <= box_height)
            {
                width_scale_ratio = Long / box_width;
                height_scale_ratio = 1;
            }
            else if (Long <= box_width && Short > box_height)
            {
                width_scale_ratio = 1;
                height_scale_ratio = Short / box_height;
            }
            else
            {
                width_scale_ratio = 1;
                height_scale_ratio = 1;
            }
        }

        public static bool IsInt(string value)
        {
            return Regex.IsMatch(value, @"^[+-]?\d*$");
        }

        public int change_font_size(float w)
        {
            int font_size = 0;
            if (w <= 50)
            {
                font_size = 10;
            }
            else if (w<100 && w>50)
            {
                font_size = 25;
            }
            else
            {
                font_size = 45;
            }
            return font_size;
        }

        public string font_horizon_or_vertical(int is_changed, float h, float w)
        {
            string return_str = null;
            if (is_changed == 0)
            {
                return_str = h.ToString() + "×" + w.ToString();
            }
            else
            {
                return_str = h.ToString() +"\r\n"+ "×" +"\r\n"+ w.ToString();
            }
            return return_str;
        }

        public MySqlConnection getMySqlCon()
        {
            String SqlConnStr = "Database='" + manufacture_db + "';Data Source='" + database_ip + "';User Id='" + database_user + "';Password='" + database_password + "';CharSet='"+charset+"'";      
            MySqlConnection mysql = new MySqlConnection(SqlConnStr);
            return mysql;
        }

        public static MySqlCommand getSqlCommand(String sql, MySqlConnection mysql)
        {
            MySqlCommand mySqlCommand = new MySqlCommand(sql, mysql);
            return mySqlCommand;
        }
       
        }

}
